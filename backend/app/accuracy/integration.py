"""
AERO RECON-3D — Accuracy Integration (Milestone 7 + 8)

Connects the accuracy framework to REAL reconstruction outputs by:

1. Loading Stage 2 feature observations (matched 2D keypoints)
2. Loading Stage 3 camera poses (R, t) and intrinsics (K)
3. Triangulating 3D points from two-view correspondences
4. Validating triangulation geometry (parallax, depth, baseline)
5. Reprojecting the triangulated 3D points back into both cameras
6. Computing reprojection error in PIXELS
7. Reporting BOTH raw and validated statistics separately

Correspondence method:
    For each accepted pair (i, j=i+1), Stage 2 produced matched 2D points
    (pt_i, pt_j). Stage 3 produced global camera poses (R_i, t_i) and
    (R_j, t_j). We triangulate a 3D world point from the two 2D
    observations using cv2.triangulatePoints with the extrinsic matrices,
    then reproject that 3D point back into both cameras using intrinsics K.

    The reprojection error per observation is:
        error = sqrt( (u_obs - u_proj)^2 + (v_obs - v_proj)^2 )

    Units: PIXELS.

    This does NOT establish metric or geospatial accuracy.

Convention (validated Milestone 3):
    X_camera = R @ X_world + t
    Projection: u = fx * Xc/Zc + cx,  v = fy * Yc/Zc + cy
    Camera center: C = -R.T @ t
"""
import pickle
import json
import math
import numpy as np
from pathlib import Path
from typing import Optional, Tuple

import cv2

from .models import (
    ReprojectionReport,
    ReprojectionStats,
    RejectionBreakdown,
    ValidationThresholds,
)


def _triangulate_points(
    K: np.ndarray,
    R1: np.ndarray, t1: np.ndarray,
    R2: np.ndarray, t2: np.ndarray,
    pts1: np.ndarray, pts2: np.ndarray,
) -> np.ndarray:
    """
    Triangulate 3D world points from two-view correspondences.

    Parameters
    ----------
    K    : 3x3 intrinsic matrix
    R1,t1: extrinsic pose for view 1 (X_cam = R @ X_world + t)
    R2,t2: extrinsic pose for view 2
    pts1 : Nx2 observed 2D points in view 1
    pts2 : Nx2 observed 2D points in view 2

    Returns
    -------
    points_3d : Nx3 world-space points (or NaN rows for failures)
    """
    P1 = K @ np.hstack([R1, t1.reshape(3, 1)])
    P2 = K @ np.hstack([R2, t2.reshape(3, 1)])

    pts1_t = pts1.T.astype(np.float64)
    pts2_t = pts2.T.astype(np.float64)

    points_4d = cv2.triangulatePoints(P1, P2, pts1_t, pts2_t)

    w = points_4d[3]
    valid = np.abs(w) > 1e-10
    points_3d = np.full((pts1.shape[0], 3), np.nan)
    points_3d[valid] = (points_4d[:3, valid] / w[valid]).T

    return points_3d


def _reproject_point(
    point_3d: np.ndarray,
    K: np.ndarray,
    R: np.ndarray,
    t: np.ndarray,
) -> Optional[np.ndarray]:
    """
    Reproject a 3D world point into image coordinates.

    X_camera = R @ X_world + t
    u = fx * Xc/Zc + cx
    v = fy * Yc/Zc + cy

    Returns None if the point is behind the camera or produces NaN.
    """
    x_cam = R @ point_3d.reshape(3, 1) + t.reshape(3, 1)
    z = x_cam[2, 0]

    if z <= 0 or not math.isfinite(z):
        return None

    fx, fy = K[0, 0], K[1, 1]
    cx, cy = K[0, 2], K[1, 2]

    u = fx * x_cam[0, 0] / z + cx
    v = fy * x_cam[1, 0] / z + cy

    if not (math.isfinite(u) and math.isfinite(v)):
        return None

    return np.array([u, v])


def _compute_parallax_angle(
    C1: np.ndarray, C2: np.ndarray, pt_3d: np.ndarray
) -> float:
    """
    Compute parallax angle (degrees) between two camera centers and a 3D point.

    The parallax angle is the angle at the 3D point in the triangle
    formed by C1, C2, and pt_3d. Larger angles give more stable triangulation.
    """
    v1 = C1.flatten() - pt_3d.flatten()
    v2 = C2.flatten() - pt_3d.flatten()

    n1 = np.linalg.norm(v1)
    n2 = np.linalg.norm(v2)

    if n1 < 1e-15 or n2 < 1e-15:
        return 0.0

    cos_angle = np.clip(np.dot(v1, v2) / (n1 * n2), -1.0, 1.0)
    return float(np.degrees(np.arccos(cos_angle)))


def _compute_stats(errors: list) -> ReprojectionStats:
    """Compute statistics from a list of error values."""
    stats = ReprojectionStats()
    if not errors:
        return stats

    arr = np.array(errors)
    stats.observation_count = len(arr)
    stats.rmse = float(np.sqrt(np.mean(arr ** 2)))
    stats.mae = float(np.mean(arr))
    stats.median = float(np.median(arr))
    stats.min_error = float(np.min(arr))
    stats.max_error = float(np.max(arr))
    stats.percentile_95 = float(np.percentile(arr, 95))
    stats.percentile_99 = float(np.percentile(arr, 99))
    return stats


def compute_real_reprojection(
    stage2_dir: Path,
    stage3_dir: Path,
    max_pairs: int = 0,
    max_matches_per_pair: int = 200,
    thresholds: Optional[ValidationThresholds] = None,
) -> ReprojectionReport:
    """
    Compute real reprojection error from pipeline artifacts.

    Returns a ReprojectionReport containing BOTH raw and validated statistics.

    Parameters
    ----------
    stage2_dir : Path to stage2/ directory containing feature_data.pkl
    stage3_dir : Path to stage3/ directory containing poses.pkl
    max_pairs  : Limit the number of pairs processed (0 = all)
    max_matches_per_pair : Cap matches per pair to limit memory/compute
    thresholds : Validation thresholds (uses defaults if None)
    """
    if thresholds is None:
        thresholds = ValidationThresholds()

    report = ReprojectionReport(
        status="REPROJECTION_UNAVAILABLE",
        thresholds=thresholds,
    )

    # ── Load Stage 2 ──────────────────────────────────────────────────────
    feature_pkl = stage2_dir / "feature_data.pkl"
    if not feature_pkl.exists():
        report.camera_intrinsics_source = "UNAVAILABLE"
        return report

    with open(feature_pkl, "rb") as f:
        feat_data = pickle.load(f)

    good_matches_list = feat_data.get("good_matches_list", [])
    if not good_matches_list:
        return report

    # ── Load Stage 3 ──────────────────────────────────────────────────────
    poses_pkl = stage3_dir / "poses.pkl"
    if not poses_pkl.exists():
        return report

    with open(poses_pkl, "rb") as f:
        pose_data = pickle.load(f)

    R_list = pose_data["R_list"]
    t_list = pose_data["t_list"]
    K = pose_data["K"]

    if K.shape != (3, 3) or not np.all(np.isfinite(K)):
        return report

    poses_json_path = stage3_dir / "camera_poses.json"
    if not poses_json_path.exists():
        return report

    with open(poses_json_path, "r") as f:
        poses_json = json.load(f)

    pose_accepted = {p["frame_idx"]: p.get("accepted", False) for p in poses_json}

    intrinsics_dict = pose_data.get("intrinsics", {})
    from .models import CameraIntrinsics
    if intrinsics_dict:
        report.camera_intrinsics = CameraIntrinsics(**intrinsics_dict)
        report.camera_intrinsics_source = report.camera_intrinsics.source
    else:
        # Fallback for old artifacts without explicitly structured intrinsics
        # We can reconstruct it from K
        cx = float(K[0, 2])
        cy = float(K[1, 2])
        f = float(K[0, 0])
        report.camera_intrinsics = CameraIntrinsics(
            width=int(cx * 2),
            height=int(cy * 2),
            fx=f,
            fy=float(K[1, 1]),
            cx=cx,
            cy=cy,
            distortion="UNAVAILABLE",
            source="ESTIMATED",
            status="ESTIMATED",
            estimation_method="focal_length_from_image_diagonal_heuristic",
            assumptions=[
                "pinhole_camera_model",
                "zero_distortion",
                "focal_length = 0.85 * max(width, height)",
                "principal_point_at_image_center"
            ]
        )
        report.camera_intrinsics_source = "ESTIMATED"

    # ── Validate poses ────────────────────────────────────────────────────
    for idx in range(len(R_list)):
        R = R_list[idx]
        if R.shape != (3, 3) or not np.all(np.isfinite(R)):
            return report
        det = np.linalg.det(R)
        if not math.isclose(det, 1.0, abs_tol=1e-3):
            return report

    for t_vec in t_list:
        if not np.all(np.isfinite(t_vec)):
            return report

    # ── Process pairs ─────────────────────────────────────────────────────
    raw_errors = []
    validated_errors = []
    rejection = RejectionBreakdown()
    total_basic_rejected = 0  # M7-compatible basic rejections

    n_pairs = len(good_matches_list)
    if max_pairs > 0:
        n_pairs = min(n_pairs, max_pairs)

    for pair_idx in range(n_pairs):
        frame_i = pair_idx
        frame_j = pair_idx + 1

        if not pose_accepted.get(frame_i, False) or not pose_accepted.get(frame_j, False):
            continue

        matches = good_matches_list[pair_idx]
        if not matches:
            continue

        if max_matches_per_pair > 0 and len(matches) > max_matches_per_pair:
            matches = matches[:max_matches_per_pair]

        R_i = np.array(R_list[frame_i], dtype=np.float64)
        t_i = np.array(t_list[frame_i], dtype=np.float64).reshape(3, 1)
        R_j = np.array(R_list[frame_j], dtype=np.float64)
        t_j = np.array(t_list[frame_j], dtype=np.float64).reshape(3, 1)

        # Camera centers: C = -R.T @ t
        C_i = (-R_i.T @ t_i).flatten()
        C_j = (-R_j.T @ t_j).flatten()
        baseline = float(np.linalg.norm(C_j - C_i))

        pts_i = np.array([[m[2][0], m[2][1]] for m in matches], dtype=np.float64)
        pts_j = np.array([[m[3][0], m[3][1]] for m in matches], dtype=np.float64)

        points_3d = _triangulate_points(K, R_i, t_i, R_j, t_j, pts_i, pts_j)

        for k in range(len(points_3d)):
            pt_3d = points_3d[k]

            # ── Check 1: finite coordinates ───────────────────────────
            if not np.all(np.isfinite(pt_3d)):
                total_basic_rejected += 1
                rejection.nonfinite_point += 1
                continue

            # ── Check 2: reproject into camera i ──────────────────────
            proj_i = _reproject_point(pt_3d, K, R_i, t_i)
            if proj_i is None:
                total_basic_rejected += 1
                rejection.behind_camera += 1
                continue

            err_i = math.sqrt(
                (pts_i[k, 0] - proj_i[0]) ** 2 +
                (pts_i[k, 1] - proj_i[1]) ** 2
            )

            # ── Check 3: reproject into camera j ──────────────────────
            proj_j = _reproject_point(pt_3d, K, R_j, t_j)
            if proj_j is None:
                total_basic_rejected += 1
                rejection.behind_camera += 1
                continue

            err_j = math.sqrt(
                (pts_j[k, 0] - proj_j[0]) ** 2 +
                (pts_j[k, 1] - proj_j[1]) ** 2
            )

            # ── Check 4: finite reprojection errors ───────────────────
            if not (math.isfinite(err_i) and math.isfinite(err_j)):
                total_basic_rejected += 2
                rejection.nonfinite_reprojection += 2
                continue

            # Both errors are valid raw observations
            raw_errors.append(err_i)
            raw_errors.append(err_j)

            # ── Geometric validation for "validated" set ──────────────

            # Parallax angle
            parallax = _compute_parallax_angle(C_i, C_j, pt_3d)

            # Depth relative to baseline
            depth_i = float((R_i @ pt_3d.reshape(3, 1) + t_i)[2, 0])
            depth_j = float((R_j @ pt_3d.reshape(3, 1) + t_j)[2, 0])
            max_depth = max(abs(depth_i), abs(depth_j))

            is_valid = True

            if parallax < thresholds.min_parallax_degrees:
                rejection.low_parallax += 2  # both observations from this point
                is_valid = False

            if baseline > 1e-15 and max_depth / baseline > thresholds.max_depth_ratio:
                rejection.excessive_depth += 2
                is_valid = False

            max_err = max(err_i, err_j)
            if max_err > thresholds.max_reprojection_error_px:
                rejection.excessive_reprojection_error += 2
                is_valid = False

            if is_valid:
                validated_errors.append(err_i)
                validated_errors.append(err_j)

    # ── Compute statistics ────────────────────────────────────────────────
    report.rejection_breakdown = rejection
    
    if not raw_errors:
        return report

    raw_stats = _compute_stats(raw_errors)
    validated_stats = _compute_stats(validated_errors)

    # Populate M7-compatible top-level fields from raw stats
    report.status = "REPROJECTION_AVAILABLE"
    report.correspondence_method = "TWO_VIEW_TRIANGULATION"
    report.valid_observations = raw_stats.observation_count
    report.rejected_observations = total_basic_rejected
    report.rmse = raw_stats.rmse
    report.mae = raw_stats.mae
    report.median = raw_stats.median
    report.min_error = raw_stats.min_error
    report.max_error = raw_stats.max_error
    report.percentile_95 = raw_stats.percentile_95
    report.percentile_99 = raw_stats.percentile_99

    # M8 extensions
    report.raw_stats = raw_stats
    report.validated_stats = validated_stats
    report.rejection_breakdown = rejection

    return report
