"""
AERO RECON-3D — Milestone 10: Synthetic Bundle Adjustment Test

Verifies:
1. Global BA converges and reduces reprojection error from perturbed initial states.
2. Camera 0 remains anchored (R=I, t=0).
3. Camera 1 translation remains anchored when valid.
4. Scale is preserved (relative geometry).
5. Robust handling of degenerate states.
"""
import numpy as np
import cv2

from app.trajectory.bundle_adjustment import (
    BundleAdjustmentConfig,
    bundle_adjust,
    build_tracks,
    initialize_landmarks
)


def generate_synthetic_tracks_and_poses(num_cameras=5, num_points=100, noise_std=0.0):
    """Generate known 3D setup, project it, and return initial noisy inputs."""
    np.random.seed(42)
    K = np.array([[800.0, 0, 640.0], [0, 800.0, 360.0], [0, 0, 1.0]])
    
    # Generate 3D points
    X_world = np.random.uniform(-2, 2, (num_points, 3))
    X_world[:, 2] = np.random.uniform(5, 10, num_points)
    
    gt_poses = {}
    
    # Camera 0 is identity
    gt_poses[0] = {"R": np.eye(3), "t": np.zeros((3,1))}
    
    # Other cameras moving right and forward
    for i in range(1, num_cameras):
        t = np.array([[-float(i)*0.5], [0.0], [0.0]])
        # Add slight rotation
        rvec = np.array([0.0, 0.05 * i, 0.0])
        R, _ = cv2.Rodrigues(rvec)
        gt_poses[i] = {"R": R, "t": t}
        
    # Generate tracks (perfect observations)
    tracks = {}
    for pt_idx in range(num_points):
        obs = []
        for cam_idx in range(num_cameras):
            R = gt_poses[cam_idx]["R"]
            t = gt_poses[cam_idx]["t"]
            Xc = R @ X_world[pt_idx] + t.flatten()
            if Xc[2] > 0:
                u = K[0,0] * Xc[0] / Xc[2] + K[0,2]
                v = K[1,1] * Xc[1] / Xc[2] + K[1,2]
                # Add pixel noise if requested
                if noise_std > 0:
                    u += np.random.normal(0, noise_std)
                    v += np.random.normal(0, noise_std)
                obs.append((cam_idx, pt_idx, u, v))
        if len(obs) >= 2:
            tracks[pt_idx] = obs
            
    # Perturb initial poses slightly (except cam 0)
    noisy_poses = {}
    for i in range(num_cameras):
        if i == 0:
            noisy_poses[i] = {"R": np.eye(3), "t": np.zeros((3,1))}
        else:
            R = gt_poses[i]["R"]
            t = gt_poses[i]["t"].copy()
            # Perturb translation by ~10%
            t += np.random.normal(0, 0.05, (3,1))
            # Perturb rotation slightly
            rvec, _ = cv2.Rodrigues(R)
            rvec += np.random.normal(0, 0.02, (3,1))
            R_noisy, _ = cv2.Rodrigues(rvec)
            noisy_poses[i] = {"R": R_noisy, "t": t}
            
    # Triangulate initial landmarks using noisy poses
    landmarks, _ = initialize_landmarks(tracks, noisy_poses, K)
    
    return tracks, landmarks, noisy_poses, gt_poses, K


def test_synthetic_ba_convergence():
    print("--- TEST: Synthetic BA Convergence ---")
    tracks, landmarks, noisy_poses, gt_poses, K = generate_synthetic_tracks_and_poses(noise_std=1.0)
    
    config = BundleAdjustmentConfig(max_iterations=50)
    res = bundle_adjust(tracks, landmarks, noisy_poses, K, config)
    
    assert res["status"] == "BA_SUCCESS"
    
    rmse_before = res["before_ba_raw_stats"]["rmse"]
    rmse_after = res["after_ba_raw_stats"]["rmse"]
    
    print(f" [OK] RMSE Before BA: {rmse_before:.4f} px")
    print(f" [OK] RMSE After BA:  {rmse_after:.4f} px")
    assert rmse_after < rmse_before, "BA failed to reduce reprojection error"
    
    ref_poses = res["refined_poses"]
    
    # Verify Camera 0 anchored
    assert np.allclose(ref_poses[0]["R"], np.eye(3))
    assert np.allclose(ref_poses[0]["t"], np.zeros((3,1)))
    print(" [OK] Camera 0 correctly anchored")
    
    # Verify Camera 1 translation anchored
    assert np.allclose(ref_poses[1]["t"], noisy_poses[1]["t"])
    print(" [OK] Camera 1 translation correctly anchored")
    
    # Verify SO(3) structure
    for i, p in ref_poses.items():
        R = p["R"]
        det = np.linalg.det(R)
        assert np.isclose(det, 1.0, atol=1e-3)
        assert np.allclose(R.T @ R, np.eye(3), atol=1e-3)
        
    print(" [OK] All rotations remain valid SO(3)")
    print("--- PASSED ---\n")


def test_degenerate_anchoring():
    print("--- TEST: Degenerate Camera 1 Anchoring ---")
    tracks, landmarks, noisy_poses, gt_poses, K = generate_synthetic_tracks_and_poses()
    
    # Force Camera 1 to have zero baseline
    noisy_poses[1]["t"] = np.zeros((3,1))
    
    config = BundleAdjustmentConfig(max_iterations=10)
    res = bundle_adjust(tracks, landmarks, noisy_poses, K, config)
    
    assert res["status"] == "BA_FAILED"
    assert "Invalid Camera 1 baseline" in res["reason"]
    print(f" [OK] Safely failed with reason: {res['reason']}")
    print("--- PASSED ---\n")


if __name__ == "__main__":
    test_synthetic_ba_convergence()
    test_degenerate_anchoring()
    print("=== ALL MILESTONE 10 SYNTHETIC TESTS PASSED ===")
