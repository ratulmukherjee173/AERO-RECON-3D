"""
AERO RECON-3D — Trajectory Refinement Integration

Bridges the raw Bundle Adjustment logic with the application artifacts.
"""
import json
import pickle
import numpy as np
from pathlib import Path
from datetime import datetime, timezone

from .bundle_adjustment import (
    build_tracks,
    initialize_landmarks,
    bundle_adjust,
    BundleAdjustmentConfig
)


def run_trajectory_refinement(job_dir: Path, config: BundleAdjustmentConfig = None):
    """
    Load artifacts, run BA, and write outputs.
    """
    if config is None:
        config = BundleAdjustmentConfig()
        
    stage2_dir = job_dir / "stage2"
    stage3_dir = job_dir / "stage3"
    out_dir = job_dir / "trajectory"
    out_dir.mkdir(parents=True, exist_ok=True)
    
    # ── Load Stage 2 ──────────────────────────────────────────────────────
    feature_pkl = stage2_dir / "feature_data.pkl"
    if not feature_pkl.exists():
        return _write_failure(out_dir, "BA_UNAVAILABLE", "Missing feature_data.pkl")
        
    with open(feature_pkl, "rb") as f:
        feat_data = pickle.load(f)
        
    good_matches_list = feat_data.get("good_matches_list", [])
    if not good_matches_list:
        return _write_failure(out_dir, "BA_UNAVAILABLE", "No matches found")
        
    # ── Load Stage 3 ──────────────────────────────────────────────────────
    poses_pkl = stage3_dir / "poses.pkl"
    if not poses_pkl.exists():
        return _write_failure(out_dir, "BA_UNAVAILABLE", "Missing poses.pkl")
        
    with open(poses_pkl, "rb") as f:
        pose_data = pickle.load(f)
        
    K = pose_data["K"]
    R_list = pose_data["R_list"]
    t_list = pose_data["t_list"]
    
    poses_json_path = stage3_dir / "camera_poses.json"
    if not poses_json_path.exists():
        return _write_failure(out_dir, "BA_UNAVAILABLE", "Missing camera_poses.json")
        
    with open(poses_json_path, "r") as f:
        poses_json = json.load(f)
        
    # Filter only accepted poses
    active_poses = {}
    for p, r, t in zip(poses_json, R_list, t_list):
        if p.get("accepted", False):
            fid = p["frame_idx"]
            active_poses[fid] = {"R": r, "t": t, "timestamp": p.get("timestamp_seconds", fid/30.0)}
            
    if len(active_poses) < 2:
        return _write_failure(out_dir, "BA_UNAVAILABLE", "Insufficient valid poses")
        
    intrinsics_dict = pose_data.get("intrinsics", {})
    intrinsics_source = intrinsics_dict.get("source", "ESTIMATED")
    
    # ── Step 1: Track Construction ────────────────────────────────────────
    tracks, track_stats = build_tracks(good_matches_list)
    if len(tracks) < 10:
        return _write_failure(out_dir, "BA_FAILED", "Insufficient valid tracks built", track_stats)
        
    # ── Step 2: Triangulation ─────────────────────────────────────────────
    landmarks, lm_stats = initialize_landmarks(tracks, active_poses, K)
    
    # ── Step 3: Bundle Adjustment ─────────────────────────────────────────
    ba_result = bundle_adjust(tracks, landmarks, active_poses, K, config)
    
    if ba_result["status"] != "BA_SUCCESS":
        return _write_failure(out_dir, ba_result["status"], ba_result["reason"], track_stats, lm_stats)
        
    # ── Trajectory Comparison ─────────────────────────────────────────────
    orig_length = 0.0
    ref_length = 0.0
    max_diff = 0.0
    diffs = []
    
    active_ids = sorted(list(active_poses.keys()))
    orig_centers = []
    ref_centers = []
    
    for i in range(len(active_ids)):
        fid = active_ids[i]
        
        orig_t = active_poses[fid]["t"]
        orig_R = active_poses[fid]["R"]
        orig_C = (-orig_R.T @ orig_t).flatten()
        orig_centers.append(orig_C)
        
        ref_t = ba_result["refined_poses"][fid]["t"]
        ref_R = ba_result["refined_poses"][fid]["R"]
        ref_C = (-ref_R.T @ ref_t).flatten()
        ref_centers.append(ref_C)
        
        diff = np.linalg.norm(orig_C - ref_C)
        diffs.append(diff)
        if diff > max_diff:
            max_diff = diff
            
        if i > 0:
            orig_length += np.linalg.norm(orig_centers[i] - orig_centers[i-1])
            ref_length += np.linalg.norm(ref_centers[i] - ref_centers[i-1])
            
    traj_comp = {
        "cameras": len(active_ids),
        "first_camera_position": ref_centers[0].tolist(),
        "last_camera_position": ref_centers[-1].tolist(),
        "original_trajectory_length": float(orig_length),
        "refined_trajectory_length": float(ref_length),
        "max_camera_displacement_diff": float(max_diff),
        "mean_camera_displacement_diff": float(np.mean(diffs)),
    }
    
    # ── Write Results ─────────────────────────────────────────────────────
    doc = {
        "job_id": job_dir.name,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": "BA_SUCCESS",
        "camera_convention": "X_camera = R @ X_world + t",
        "intrinsics_source": intrinsics_source,
        "track_statistics": track_stats,
        "landmark_statistics": lm_stats,
        "optimization_configuration": {
            "optimizer": ba_result["optimizer"],
            "scipy_version": ba_result["scipy_version"],
            "huber_delta": config.huber_delta,
            "max_iterations": config.max_iterations,
        },
        "convergence_status": {
            "iterations": ba_result["iterations"],
            "message": ba_result["message"]
        },
        "before_ba_metrics": ba_result["before_ba_raw_stats"],
        "after_ba_metrics": ba_result["after_ba_raw_stats"],
        "trajectory_comparison": traj_comp,
        "limitations": [
            "IMAGE_SPACE_CONSISTENCY_ONLY",
            "RELATIVE_COORDINATES",
            "METRIC_SCALE_UNAVAILABLE",
            "GPS_IMU_UNAVAILABLE"
        ]
    }
    
    out_file = out_dir / f"{job_dir.name}_bundle_adjustment.json"
    with open(out_file, "w") as f:
        json.dump(doc, f, indent=2)
        
    # Write refined trajectory
    refined_traj = []
    for fid in active_ids:
        ref = ba_result["refined_poses"][fid]
        ref_C = (-ref["R"].T @ ref["t"]).flatten()
        refined_traj.append({
            "frame_idx": fid,
            "timestamp_seconds": active_poses[fid]["timestamp"],
            "R": ref["R"].tolist(),
            "t": ref["t"].flatten().tolist(),
            "C": ref_C.tolist(),
            "accepted": True,
            "coordinate_system": "RELATIVE",
            "metric_scale": "UNAVAILABLE"
        })
        
    with open(out_dir / "refined_camera_trajectory.json", "w") as f:
        json.dump(refined_traj, f, indent=2)
        
    return doc


def _write_failure(out_dir: Path, status: str, reason: str, tracks=None, landmarks=None):
    doc = {
        "status": status,
        "reason": reason,
        "track_statistics": tracks,
        "landmark_statistics": landmarks
    }
    with open(out_dir / "bundle_adjustment_failure.json", "w") as f:
        json.dump(doc, f, indent=2)
    return doc
