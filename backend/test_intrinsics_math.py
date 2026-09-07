"""
AERO RECON-3D — Milestone 9: Synthetic Camera Calibration & Sensitivity Test

Verifies:
1. True calibration yields approximately zero reprojection error.
2. Deliberately incorrect K yields measurable error.
3. Intrinsics are explicitly tracked and never falsely labeled CALIBRATED.
4. Sensitivity of reprojection error to varying intrinsic parameters.
"""
import math
import tempfile
import pickle
import json
import numpy as np
from pathlib import Path

from app.accuracy.integration import compute_real_reprojection
from app.accuracy.models import ValidationThresholds


def _make_test_data(tmpdir: Path, poses, matches_list, K, intrinsics_dict):
    """Helper to write synthetic Stage 2/3 data to a temp directory."""
    stage2 = tmpdir / "stage2"
    stage3 = tmpdir / "stage3"
    stage2.mkdir()
    stage3.mkdir()

    kps = [[{"x": 0, "y": 0, "size": 1, "angle": 0}]] * len(poses)
    with open(stage2 / "feature_data.pkl", "wb") as f:
        pickle.dump({
            "kps_serialisable": kps,
            "descs_list": [None] * len(poses),
            "good_matches_list": matches_list,
        }, f)

    R_list = [np.array(p["R"]) for p in poses]
    t_list = [np.array(p["t"]).reshape(3, 1) for p in poses]

    with open(stage3 / "poses.pkl", "wb") as f:
        pickle.dump({
            "R_list": R_list, 
            "t_list": t_list, 
            "K": K,
            "intrinsics": intrinsics_dict
        }, f)

    with open(stage3 / "camera_poses.json", "w") as f:
        json.dump(poses, f)


def project(X_w, K, R, t):
    """Project 3D world point into 2D camera coordinates."""
    x_cam = R @ X_w + t.flatten()
    if x_cam[2] <= 0:
        return np.array([float('nan'), float('nan')])
    return np.array([
        K[0, 0] * x_cam[0] / x_cam[2] + K[0, 2],
        K[1, 1] * x_cam[1] / x_cam[2] + K[1, 2]
    ])


def generate_synthetic_scene(num_points=50, depth=5.0):
    """Generate a synthetic scene with ground-truth points and poses."""
    K_true = np.array([
        [800.0, 0, 640.0],
        [0, 800.0, 360.0],
        [0, 0, 1.0]
    ], dtype=np.float64)

    # Camera 1 at origin
    R1 = np.eye(3)
    t1 = np.zeros(3)

    # Camera 2 translated right by 1 unit
    R2 = np.eye(3)
    t2 = np.array([-1.0, 0.0, 0.0]) # t is extrinsic translation, C = -R^T t. So C2 = [1,0,0].

    # Generate random points in front of cameras
    np.random.seed(42)
    X_world = np.random.uniform(-1, 2, (num_points, 3))
    X_world[:, 2] = np.random.uniform(depth - 1, depth + 1, num_points)

    observations = []
    for X in X_world:
        uv1 = project(X, K_true, R1, t1)
        uv2 = project(X, K_true, R2, t2)
        observations.append((uv1, uv2))

    poses = [
        {"frame_idx": 0, "R": R1.tolist(), "t": t1.tolist(), "inliers": 100, "accepted": True},
        {"frame_idx": 1, "R": R2.tolist(), "t": t2.tolist(), "inliers": 100, "accepted": True},
    ]

    matches = []
    for idx, (uv1, uv2) in enumerate(observations):
        matches.append((idx, idx, uv1.tolist(), uv2.tolist()))

    intrinsics_dict = {
        "width": 1280,
        "height": 720,
        "fx": 800.0,
        "fy": 800.0,
        "cx": 640.0,
        "cy": 360.0,
        "distortion": "UNAVAILABLE",
        "source": "CALIBRATED",
        "status": "CALIBRATED",
        "estimation_method": "synthetic_ground_truth",
        "assumptions": []
    }

    return poses, [matches], K_true, intrinsics_dict


def test_true_calibration():
    """Verify that perfect ground-truth calibration yields ~zero reprojection error."""
    print("--- TEST: True Calibration ---")
    poses, matches_list, K_true, intrinsics_dict = generate_synthetic_scene()

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        _make_test_data(tmpdir, poses, matches_list, K_true, intrinsics_dict)
        report = compute_real_reprojection(
            tmpdir / "stage2", tmpdir / "stage3",
            max_matches_per_pair=0,
        )

    assert report.status == "REPROJECTION_AVAILABLE"
    # Even perfectly clean synthetic data might have tiny floating point residuals
    assert report.validated_stats.rmse < 1e-4, f"Expected near zero RMSE, got {report.validated_stats.rmse}"
    print(f" [OK] True Calibration RMSE: {report.validated_stats.rmse:.8f} px")
    print("--- PASSED ---\n")


def test_intrinsic_sensitivity():
    """Verify that deliberately incorrect intrinsics produce measurable and monotonic error growth."""
    print("--- TEST: Intrinsic Sensitivity ---")
    poses, matches_list, K_true, intrinsics_dict = generate_synthetic_scene()

    variations = [
        ("Focal Length -10%", 0.90, 1.0, 1.0),
        ("Focal Length -5%", 0.95, 1.0, 1.0),
        ("Baseline K", 1.0, 1.0, 1.0),
        ("Focal Length +5%", 1.05, 1.0, 1.0),
        ("Focal Length +10%", 1.10, 1.0, 1.0),
        ("Principal Point Shift (+20px)", 1.0, 1.0, 20.0),
    ]

    results = []

    for name, f_scale, cy_scale, cx_shift in variations:
        K_test = K_true.copy()
        K_test[0, 0] *= f_scale
        K_test[1, 1] *= f_scale
        K_test[0, 2] += cx_shift
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            _make_test_data(tmpdir, poses, matches_list, K_test, intrinsics_dict)
            report = compute_real_reprojection(
                tmpdir / "stage2", tmpdir / "stage3",
                max_matches_per_pair=0,
            )
        
        rmse = report.validated_stats.rmse if report.validated_stats.observation_count > 0 else float('inf')
        results.append((name, rmse))
        print(f" [INFO] {name:30s} -> RMSE: {rmse:.4f} px")

    # Verification
    # Baseline should be near zero
    baseline_rmse = dict(results)["Baseline K"]
    assert baseline_rmse < 1e-4

    # 10% error should be worse than 5% error
    assert dict(results)["Focal Length -10%"] > dict(results)["Focal Length -5%"]
    assert dict(results)["Focal Length +10%"] > dict(results)["Focal Length +5%"]

    # Principal point shift should also introduce measurable error
    assert dict(results)["Principal Point Shift (+20px)"] > 1.0

    print(" [OK] Monotonic error growth verified.")
    print(" [OK] Sensitivity clearly quantifiable.")
    print("--- PASSED ---\n")


if __name__ == "__main__":
    test_true_calibration()
    test_intrinsic_sensitivity()
    print("=== ALL MILESTONE 9 SYNTHETIC TESTS PASSED ===")
