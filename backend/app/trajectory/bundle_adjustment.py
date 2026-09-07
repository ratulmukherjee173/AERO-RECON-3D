"""
AERO RECON-3D — Global Bundle Adjustment Module

Performs global trajectory refinement using robust nonlinear optimization
of camera poses and 3D landmarks (Bundle Adjustment).
Preserves the relative coordinate system convention:
    X_camera = R X_world + t
"""
import math
import numpy as np
import cv2
from scipy.optimize import least_squares
from scipy.sparse import lil_matrix
from typing import Dict, List, Tuple, Optional
from collections import defaultdict


class BundleAdjustmentConfig:
    def __init__(
        self,
        huber_delta: float = 1.0,
        max_iterations: int = 100,
        ftol: float = 1e-4,
        xtol: float = 1e-4,
        verbose: int = 2
    ):
        self.huber_delta = huber_delta
        self.max_iterations = max_iterations
        self.ftol = ftol
        self.xtol = xtol
        self.verbose = verbose


def build_tracks(good_matches_list: List[List], min_track_length: int = 2) -> Tuple[Dict[int, List], Dict]:
    """
    Construct global feature tracks from sequential pairwise matches.
    
    A track is a unique physical 3D point.
    Returns:
        tracks: dict mapping track_id -> list of (frame_idx, kp_idx, pt_x, pt_y)
        stats: dict of track construction statistics
    """
    # map (frame_idx, kp_idx) -> track_id
    kp_to_track = {}
    tracks = defaultdict(list)
    next_track_id = 0
    
    # Matches list is a list of pairs. pair_idx i is frames (i, i+1).
    for pair_idx, matches in enumerate(good_matches_list):
        frame_i = pair_idx
        frame_j = pair_idx + 1
        
        for m in matches:
            # Format: (queryIdx, trainIdx, [x_i, y_i], [x_j, y_j])
            if len(m) != 4:
                continue
            kp_i_idx, kp_j_idx, pt_i, pt_j = m
            
            key_i = (frame_i, kp_i_idx)
            key_j = (frame_j, kp_j_idx)
            
            track_id_i = kp_to_track.get(key_i)
            track_id_j = kp_to_track.get(key_j)
            
            if track_id_i is None and track_id_j is None:
                # New track
                t_id = next_track_id
                next_track_id += 1
                kp_to_track[key_i] = t_id
                kp_to_track[key_j] = t_id
                tracks[t_id].append((frame_i, kp_i_idx, pt_i[0], pt_i[1]))
                tracks[t_id].append((frame_j, kp_j_idx, pt_j[0], pt_j[1]))
            elif track_id_i is not None and track_id_j is None:
                # Add to existing track i
                t_id = track_id_i
                kp_to_track[key_j] = t_id
                tracks[t_id].append((frame_j, kp_j_idx, pt_j[0], pt_j[1]))
            elif track_id_i is None and track_id_j is not None:
                # Add to existing track j
                t_id = track_id_j
                kp_to_track[key_i] = t_id
                tracks[t_id].append((frame_i, kp_i_idx, pt_i[0], pt_i[1]))
            else:
                # Merge tracks if they differ
                if track_id_i != track_id_j:
                    t_keep = track_id_i
                    t_merge = track_id_j
                    for obs in tracks[t_merge]:
                        obs_key = (obs[0], obs[1])
                        kp_to_track[obs_key] = t_keep
                        tracks[t_keep].append(obs)
                    del tracks[t_merge]

    # Validate tracks:
    # 1. Reject if track contains multiple observations from the same frame
    # 2. Reject if track length < min_track_length
    valid_tracks = {}
    rejected_conflict = 0
    rejected_short = 0
    
    for t_id, obs_list in tracks.items():
        frames_in_track = [obs[0] for obs in obs_list]
        if len(frames_in_track) != len(set(frames_in_track)):
            rejected_conflict += 1
            continue
        if len(obs_list) < min_track_length:
            rejected_short += 1
            continue
            
        # Re-index to be consecutive valid tracks
        valid_tracks[len(valid_tracks)] = sorted(obs_list, key=lambda x: x[0])
        
    stats = {
        "total_tracks_built": len(tracks),
        "valid_tracks": len(valid_tracks),
        "rejected_conflict": rejected_conflict,
        "rejected_short": rejected_short,
        "observations_used": sum(len(obs) for obs in valid_tracks.values())
    }
    
    return valid_tracks, stats


def triangulate_multiview(K, poses, track_obs):
    """
    Simple robust 2-view triangulation for multi-view tracks.
    Uses the first and last observation in the track for maximal baseline.
    Returns 3D point or None if invalid.
    """
    if len(track_obs) < 2:
        return None
        
    # Use first and last observation
    obs1 = track_obs[0]
    obs2 = track_obs[-1]
    
    f1, _, x1, y1 = obs1
    f2, _, x2, y2 = obs2
    
    if f1 not in poses or f2 not in poses:
        return None
        
    R1 = poses[f1]["R"]
    t1 = poses[f1]["t"]
    R2 = poses[f2]["R"]
    t2 = poses[f2]["t"]
    
    P1 = K @ np.hstack((R1, t1))
    P2 = K @ np.hstack((R2, t2))
    
    pt1 = np.array([[x1], [y1]], dtype=np.float64)
    pt2 = np.array([[x2], [y2]], dtype=np.float64)
    
    pt4d = cv2.triangulatePoints(P1, P2, pt1, pt2)
    pt3d = pt4d[:3] / pt4d[3]
    pt3d = pt3d.flatten()
    
    if not np.all(np.isfinite(pt3d)):
        return None
        
    # Check if behind either camera
    cam1_pt = R1 @ pt3d + t1.flatten()
    cam2_pt = R2 @ pt3d + t2.flatten()
    if cam1_pt[2] <= 0 or cam2_pt[2] <= 0:
        return None
        
    return pt3d


def initialize_landmarks(tracks, poses, K):
    """
    Triangulate valid tracks using initial poses.
    Returns:
        landmarks: dict of track_id -> [X, Y, Z]
        stats: dict of landmark stats
    """
    landmarks = {}
    rejected_nonfinite = 0
    rejected_behind_cam = 0
    
    for t_id, obs_list in tracks.items():
        pt3d = triangulate_multiview(K, poses, obs_list)
        if pt3d is not None:
            landmarks[t_id] = pt3d
        else:
            rejected_behind_cam += 1
            
    stats = {
        "initial_landmarks": len(landmarks),
        "rejected_nonfinite_or_behind": rejected_behind_cam,
    }
    return landmarks, stats


def reprojection_residuals(params, n_cameras, n_points, camera_indices, point_indices, points_2d, K, fix_t1, t1_initial):
    """
    Residual function for bundle adjustment.
    
    params: 1D array of parameters
        - cameras 1..n_cameras-1: [r1, r2, r3, t1, t2, t3] (except Camera 1 might have t fixed)
        - points 0..n_points-1: [X, Y, Z]
    """
    # Reconstruct cameras
    cam_params_end = (n_cameras - 1) * 6
    if fix_t1:
        cam_params_end -= 3
        
    camera_params = params[:cam_params_end]
    points_3d = params[cam_params_end:].reshape((n_points, 3))
    
    # We will build an array of shape (n_cameras, 6) for all cameras
    # Camera 0 is always [0,0,0, 0,0,0] (Identity, zero translation)
    all_cam_params = np.zeros((n_cameras, 6))
    
    idx = 0
    for i in range(1, n_cameras):
        if i == 1 and fix_t1:
            # Rotation is optimized, translation is fixed
            all_cam_params[i, :3] = camera_params[idx:idx+3]
            all_cam_params[i, 3:] = t1_initial
            idx += 3
        else:
            all_cam_params[i, :] = camera_params[idx:idx+6]
            idx += 6
            
    # Project points
    # Extract params for the specific observations
    obs_cam_params = all_cam_params[camera_indices]
    obs_points_3d = points_3d[point_indices]
    
    projected = np.zeros((len(points_2d), 2))
    
    for i in range(len(points_2d)):
        rvec = obs_cam_params[i, :3]
        tvec = obs_cam_params[i, 3:]
        X = obs_points_3d[i]
        
        R, _ = cv2.Rodrigues(rvec)
        Xc = R @ X + tvec
        
        # Prevent division by zero
        z = Xc[2] if abs(Xc[2]) > 1e-6 else 1e-6
        
        u = K[0, 0] * (Xc[0] / z) + K[0, 2]
        v = K[1, 1] * (Xc[1] / z) + K[1, 2]
        
        projected[i, 0] = u
        projected[i, 1] = v
        
    return (projected - points_2d).ravel()


def bundle_adjust(tracks, landmarks, poses, K, config: BundleAdjustmentConfig):
    """
    Perform global bundle adjustment.
    """
    if len(landmarks) < 10:
        return {"status": "BA_FAILED", "reason": "Insufficient landmarks"}
        
    # Find active cameras (those with at least one observation of a valid landmark)
    # Re-index cameras and points for the optimizer
    active_frame_ids = sorted(list(poses.keys()))
    frame_to_idx = {fid: i for i, fid in enumerate(active_frame_ids)}
    
    active_track_ids = sorted(list(landmarks.keys()))
    track_to_idx = {tid: i for i, tid in enumerate(active_track_ids)}
    
    n_cameras = len(active_frame_ids)
    n_points = len(active_track_ids)
    
    # ── Verify Camera 1 Baseline ──────────────────────────────────────────
    fix_t1 = False
    t1_initial = None
    if n_cameras >= 2:
        frame1_id = active_frame_ids[1]
        t1 = poses[frame1_id]["t"].flatten()
        C0 = np.zeros(3)
        R1 = poses[frame1_id]["R"]
        C1 = -R1.T @ t1
        baseline = np.linalg.norm(C1 - C0)
        
        if np.isfinite(baseline) and baseline > 1e-3:
            fix_t1 = True
            t1_initial = t1.copy()
        else:
            return {"status": "BA_FAILED", "reason": f"Invalid Camera 1 baseline ({baseline})"}
            
    # ── Initialise Parameter Vector ───────────────────────────────────────
    # Camera 0 is fixed.
    # Camera 1 has 3 params if fix_t1, else 6
    # Other cameras have 6 params.
    n_cam_params = (n_cameras - 1) * 6
    if fix_t1:
        n_cam_params -= 3
        
    x0 = np.empty(n_cam_params + n_points * 3)
    
    idx = 0
    for i in range(1, n_cameras):
        fid = active_frame_ids[i]
        R = poses[fid]["R"]
        t = poses[fid]["t"].flatten()
        rvec, _ = cv2.Rodrigues(R)
        rvec = rvec.flatten()
        
        if i == 1 and fix_t1:
            x0[idx:idx+3] = rvec
            idx += 3
        else:
            x0[idx:idx+3] = rvec
            x0[idx+3:idx+6] = t
            idx += 6
            
    for i in range(n_points):
        tid = active_track_ids[i]
        x0[n_cam_params + i * 3 : n_cam_params + i * 3 + 3] = landmarks[tid]
        
    # ── Gather Observations ───────────────────────────────────────────────
    camera_indices = []
    point_indices = []
    points_2d = []
    
    for tid in active_track_ids:
        p_idx = track_to_idx[tid]
        for obs in tracks[tid]:
            fid = obs[0]
            if fid in frame_to_idx:
                c_idx = frame_to_idx[fid]
                camera_indices.append(c_idx)
                point_indices.append(p_idx)
                points_2d.append([obs[2], obs[3]])
                
    camera_indices = np.array(camera_indices)
    point_indices = np.array(point_indices)
    points_2d = np.array(points_2d)
    
    # ── Build Sparse Jacobian Matrix ──────────────────────────────────────
    m = camera_indices.size * 2
    n = x0.size
    A = lil_matrix((m, n), dtype=int)
    
    # Each observation gives 2 residuals.
    # It depends on 6 camera params (or 3 for cam1) and 3 point params.
    for i in range(camera_indices.size):
        c_idx = camera_indices[i]
        p_idx = point_indices[i]
        
        # Camera derivatives
        if c_idx > 0:
            if fix_t1:
                if c_idx == 1:
                    c_param_start = 0
                    c_param_end = 3
                else:
                    c_param_start = 3 + (c_idx - 2) * 6
                    c_param_end = c_param_start + 6
            else:
                c_param_start = (c_idx - 1) * 6
                c_param_end = c_param_start + 6
                
            A[2 * i, c_param_start:c_param_end] = 1
            A[2 * i + 1, c_param_start:c_param_end] = 1
            
        # Point derivatives
        p_param_start = n_cam_params + p_idx * 3
        p_param_end = p_param_start + 3
        A[2 * i, p_param_start:p_param_end] = 1
        A[2 * i + 1, p_param_start:p_param_end] = 1
        
    # ── Run Optimization ──────────────────────────────────────────────────
    import scipy
    try:
        res = least_squares(
            reprojection_residuals, x0,
            jac_sparsity=A,
            verbose=config.verbose,
            x_scale='jac',
            ftol=config.ftol,
            xtol=config.xtol,
            method='trf',
            loss='huber',
            f_scale=config.huber_delta,
            args=(n_cameras, n_points, camera_indices, point_indices, points_2d, K, fix_t1, t1_initial)
        )
    except Exception as e:
        return {"status": "BA_FAILED", "reason": f"Optimization exception: {str(e)}"}
        
    if not res.success and res.status <= 0:
        return {"status": "BA_FAILED", "reason": f"Optimization failed: {res.message}"}
        
    # ── Reconstruct Results ───────────────────────────────────────────────
    refined_poses = {}
    
    # Camera 0 is fixed
    refined_poses[active_frame_ids[0]] = {
        "R": np.eye(3),
        "t": np.zeros((3, 1))
    }
    
    idx = 0
    for i in range(1, n_cameras):
        fid = active_frame_ids[i]
        
        if i == 1 and fix_t1:
            rvec = res.x[idx:idx+3]
            tvec = t1_initial.copy()
            idx += 3
        else:
            rvec = res.x[idx:idx+3]
            tvec = res.x[idx+3:idx+6]
            idx += 6
            
        R, _ = cv2.Rodrigues(rvec)
        
        # Validate SO(3)
        det = np.linalg.det(R)
        ortho_err = np.linalg.norm(R.T @ R - np.eye(3))
        if not np.isclose(det, 1.0, atol=1e-3) or ortho_err > 1e-3:
            return {"status": "BA_FAILED", "reason": f"Invalid SO(3) matrix generated for camera {fid}"}
            
        refined_poses[fid] = {
            "R": R,
            "t": tvec.reshape(3, 1)
        }
        
    refined_landmarks = {}
    for i in range(n_points):
        tid = active_track_ids[i]
        pt = res.x[n_cam_params + i * 3 : n_cam_params + i * 3 + 3]
        if not np.all(np.isfinite(pt)):
            return {"status": "BA_FAILED", "reason": "Optimization generated non-finite landmarks"}
        refined_landmarks[tid] = pt
        
    # Compute initial and final residuals for stats
    f0 = reprojection_residuals(x0, n_cameras, n_points, camera_indices, point_indices, points_2d, K, fix_t1, t1_initial)
    fn = res.fun
    
    def compute_stats(residuals):
        errs = np.abs(residuals)  # errors are in x and y, combine them?
        # Actually residuals is 1D [dx1, dy1, dx2, dy2, ...]
        errs_2d = np.linalg.norm(residuals.reshape(-1, 2), axis=1)
        return {
            "observations": len(errs_2d),
            "mae": float(np.mean(errs_2d)),
            "median": float(np.median(errs_2d)),
            "rmse": float(np.sqrt(np.mean(errs_2d**2))),
            "p95": float(np.percentile(errs_2d, 95)),
            "p99": float(np.percentile(errs_2d, 99)),
            "max": float(np.max(errs_2d))
        }

    return {
        "status": "BA_SUCCESS",
        "refined_poses": refined_poses,
        "refined_landmarks": refined_landmarks,
        "before_ba_raw_stats": compute_stats(f0),
        "after_ba_raw_stats": compute_stats(fn),
        "optimizer": "scipy.optimize.least_squares",
        "scipy_version": scipy.__version__,
        "iterations": res.nfev,
        "message": res.message
    }
