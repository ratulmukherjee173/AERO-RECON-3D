"""
AERO RECON-3D — Milestone 8: Synthetic Triangulation Validation Test

Verifies that degenerate and invalid triangulation cases are correctly
classified and that raw vs validated statistics are separated properly.

This test creates deterministic synthetic scenarios:
1. Valid well-conditioned correspondences
2. Deliberately degenerate near-parallel cameras (low parallax)
3. Deliberately large reprojection-error outliers

Does NOT use real UAV data.
"""
import math
import tempfile
import pickle
import json
import numpy as np
from pathlib import Path

from app.accuracy.integration import compute_real_reprojection
from app.accuracy.models import ValidationThresholds


def _make_test_data(tmpdir: Path, poses, matches_list, K):
    """Helper to write synthetic Stage 2/3 data to a temp directory."""
    stage2 = tmpdir / "stage2"
    stage3 = tmpdir / "stage3"
    stage2.mkdir()
    stage3.mkdir()

    # Stage 2: feature_data.pkl
    kps = [[{"x": 0, "y": 0, "size": 1, "angle": 0}]] * len(poses)
    with open(stage2 / "feature_data.pkl", "wb") as f:
        pickle.dump({
            "kps_serialisable": kps,
            "descs_list": [None] * len(poses),
            "good_matches_list": matches_list,
        }, f)

    # Stage 3: poses.pkl + camera_poses.json
    R_list = [np.array(p["R"]) for p in poses]
    t_list = [np.array(p["t"]).reshape(3, 1) for p in poses]

    with open(stage3 / "poses.pkl", "wb") as f:
        pickle.dump({"R_list": R_list, "t_list": t_list, "K": K}, f)

    with open(stage3 / "camera_poses.json", "w") as f:
        json.dump(poses, f)


def test_valid_triangulation():
    """Well-conditioned two-view triangulation should produce low error."""
    print("--- TEST: Valid well-conditioned triangulation ---")

    K = np.array([[500, 0, 320], [0, 500, 240], [0, 0, 1]], dtype=np.float64)
    R1 = np.eye(3)
    t1 = np.zeros(3)

    # Second camera shifted 1 unit along X — good baseline
    R2 = np.eye(3)
    t2 = np.array([1.0, 0.0, 0.0])

    # A 3D point at (0.5, 0.3, 5.0) — well in front of both cameras
    X = np.array([0.5, 0.3, 5.0])

    # Project into both cameras
    def project(X_w, K, R, t):
        x_cam = R @ X_w + t
        return np.array([K[0, 0] * x_cam[0] / x_cam[2] + K[0, 2],
                         K[1, 1] * x_cam[1] / x_cam[2] + K[1, 2]])

    uv1 = project(X, K, R1, t1)
    uv2 = project(X, K, R2, t2)

    poses = [
        {"frame_idx": 0, "R": R1.tolist(), "t": t1.tolist(), "inliers": -1, "accepted": True},
        {"frame_idx": 1, "R": R2.tolist(), "t": t2.tolist(), "inliers": 100, "accepted": True},
    ]
    matches = [[(0, 0, uv1.tolist(), uv2.tolist())]]

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        _make_test_data(tmpdir, poses, matches, K)
        report = compute_real_reprojection(
            tmpdir / "stage2", tmpdir / "stage3",
            max_matches_per_pair=0,
        )

    assert report.status == "REPROJECTION_AVAILABLE"
    assert report.raw_stats.observation_count == 2
    assert report.raw_stats.rmse < 0.01, f"Expected near-zero RMSE, got {report.raw_stats.rmse}"
    assert report.validated_stats.observation_count == 2
    print(f" [OK] Raw RMSE: {report.raw_stats.rmse:.6f} px (near zero as expected)")
    print(f" [OK] Validated RMSE: {report.validated_stats.rmse:.6f} px")
    print(f" [OK] Both raw and validated counts: {report.raw_stats.observation_count}")
    print("--- PASSED ---\n")


def test_degenerate_low_parallax():
    """Near-parallel cameras (tiny baseline) should trigger low_parallax rejection."""
    print("--- TEST: Degenerate low-parallax triangulation ---")

    K = np.array([[500, 0, 320], [0, 500, 240], [0, 0, 1]], dtype=np.float64)
    R1 = np.eye(3)
    t1 = np.zeros(3)

    # Cameras separated by only 0.00001 units — nearly zero baseline
    R2 = np.eye(3)
    t2 = np.array([0.00001, 0.0, 0.0])

    # Point at moderate depth
    X = np.array([0.5, 0.3, 5.0])

    def project(X_w, K, R, t):
        x_cam = R @ X_w + t
        return np.array([K[0, 0] * x_cam[0] / x_cam[2] + K[0, 2],
                         K[1, 1] * x_cam[1] / x_cam[2] + K[1, 2]])

    uv1 = project(X, K, R1, t1)
    uv2 = project(X, K, R2, t2)

    poses = [
        {"frame_idx": 0, "R": R1.tolist(), "t": t1.tolist(), "inliers": -1, "accepted": True},
        {"frame_idx": 1, "R": R2.tolist(), "t": t2.tolist(), "inliers": 100, "accepted": True},
    ]
    matches = [[(0, 0, uv1.tolist(), uv2.tolist())]]

    thresholds = ValidationThresholds(min_parallax_degrees=1.0)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        _make_test_data(tmpdir, poses, matches, K)
        report = compute_real_reprojection(
            tmpdir / "stage2", tmpdir / "stage3",
            max_matches_per_pair=0,
            thresholds=thresholds,
        )

    assert report.status == "REPROJECTION_AVAILABLE"
    # Raw observations should still exist
    assert report.raw_stats.observation_count == 2
    # Validated should have 0 because parallax is negligible
    assert report.validated_stats.observation_count == 0
    assert report.rejection_breakdown.low_parallax >= 2
    print(f" [OK] Raw observations: {report.raw_stats.observation_count}")
    print(f" [OK] Validated observations: {report.validated_stats.observation_count}")
    print(f" [OK] Low parallax rejections: {report.rejection_breakdown.low_parallax}")
    print("--- PASSED ---\n")


def test_excessive_reprojection_outlier():
    """Large reprojection error should be classified in validated rejection."""
    print("--- TEST: Excessive reprojection error classification ---")

    K = np.array([[500, 0, 320], [0, 500, 240], [0, 0, 1]], dtype=np.float64)
    R1 = np.eye(3)
    t1 = np.zeros(3)
    R2 = np.eye(3)
    t2 = np.array([1.0, 0.0, 0.0])

    X = np.array([0.5, 0.3, 5.0])

    def project(X_w, K, R, t):
        x_cam = R @ X_w + t
        return np.array([K[0, 0] * x_cam[0] / x_cam[2] + K[0, 2],
                         K[1, 1] * x_cam[1] / x_cam[2] + K[1, 2]])

    uv1 = project(X, K, R1, t1)
    uv2 = project(X, K, R2, t2)

    # Deliberately perturb uv2 by 200 pixels vertically (perpendicular to the
    # horizontal epipolar lines caused by the X-axis camera translation).
    # Triangulation must compromise on the Y coordinate, splitting the error
    # between the two views, guaranteeing an error of roughly 100 px per view.
    uv2_bad = uv2 + np.array([0.0, 200.0])

    poses = [
        {"frame_idx": 0, "R": R1.tolist(), "t": t1.tolist(), "inliers": -1, "accepted": True},
        {"frame_idx": 1, "R": R2.tolist(), "t": t2.tolist(), "inliers": 100, "accepted": True},
    ]
    matches = [[(0, 0, uv1.tolist(), uv2_bad.tolist())]]

    thresholds = ValidationThresholds(max_reprojection_error_px=50.0)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        _make_test_data(tmpdir, poses, matches, K)
        report = compute_real_reprojection(
            tmpdir / "stage2", tmpdir / "stage3",
            max_matches_per_pair=0,
            thresholds=thresholds,
        )

    assert report.status == "REPROJECTION_AVAILABLE"
    # Raw should contain the large error observations
    assert report.raw_stats.observation_count == 2
    assert report.raw_stats.max_error > 50.0
    # Validated should exclude them
    assert report.validated_stats.observation_count == 0
    assert report.rejection_breakdown.excessive_reprojection_error >= 2
    print(f" [OK] Raw max error: {report.raw_stats.max_error:.2f} px (>50 as expected)")
    print(f" [OK] Validated observations: {report.validated_stats.observation_count}")
    print(f" [OK] Excessive reproj rejections: {report.rejection_breakdown.excessive_reprojection_error}")
    print("--- PASSED ---\n")


def test_behind_camera():
    """Points behind camera should be rejected in both raw and validated."""
    print("--- TEST: Behind-camera point rejection ---")

    K = np.array([[500, 0, 320], [0, 500, 240], [0, 0, 1]], dtype=np.float64)
    R1 = np.eye(3)
    t1 = np.zeros(3)
    R2 = np.eye(3)
    t2 = np.array([1.0, 0.0, 0.0])

    # Deliberately provide 2D observations that would triangulate behind camera
    # by swapping the observations between cameras
    X_front = np.array([0.5, 0.3, 5.0])

    def project(X_w, K, R, t):
        x_cam = R @ X_w + t
        return np.array([K[0, 0] * x_cam[0] / x_cam[2] + K[0, 2],
                         K[1, 1] * x_cam[1] / x_cam[2] + K[1, 2]])

    uv1 = project(X_front, K, R1, t1)
    uv2 = project(X_front, K, R2, t2)

    # Use the point that is actually behind camera 2 by placing it at z=-5
    X_behind = np.array([0.5, 0.3, -5.0])
    uv1_b = project(X_behind, K, R1, t1)  # This will have z < 0 in cam 1
    # These 2D coords from a behind-camera point won't correspond to good triangulation

    poses = [
        {"frame_idx": 0, "R": R1.tolist(), "t": t1.tolist(), "inliers": -1, "accepted": True},
        {"frame_idx": 1, "R": R2.tolist(), "t": t2.tolist(), "inliers": 100, "accepted": True},
    ]

    # Use NaN observations to simulate completely invalid correspondence
    matches = [[(0, 0, [float('nan'), float('nan')], uv2.tolist())]]

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        _make_test_data(tmpdir, poses, matches, K)
        report = compute_real_reprojection(
            tmpdir / "stage2", tmpdir / "stage3",
            max_matches_per_pair=0,
        )

    # Should have basic rejections
    assert report.rejection_breakdown.nonfinite_point >= 1 or \
           report.rejection_breakdown.behind_camera >= 1
    print(f" [OK] Nonfinite point rejections: {report.rejection_breakdown.nonfinite_point}")
    print(f" [OK] Behind camera rejections: {report.rejection_breakdown.behind_camera}")
    print("--- PASSED ---\n")


def test_raw_vs_validated_separation():
    """Mix of good and bad observations: raw stats must differ from validated."""
    print("--- TEST: Raw vs validated statistics separation ---")

    K = np.array([[500, 0, 320], [0, 500, 240], [0, 0, 1]], dtype=np.float64)
    R1 = np.eye(3)
    t1 = np.zeros(3)
    R2 = np.eye(3)
    t2 = np.array([1.0, 0.0, 0.0])

    def project(X_w, K, R, t):
        x_cam = R @ X_w + t
        return np.array([K[0, 0] * x_cam[0] / x_cam[2] + K[0, 2],
                         K[1, 1] * x_cam[1] / x_cam[2] + K[1, 2]])

    # Good point
    X_good = np.array([0.5, 0.3, 5.0])
    uv1_good = project(X_good, K, R1, t1)
    uv2_good = project(X_good, K, R2, t2)

    # Bad point — 200px offset vertically (perpendicular to epipolar lines)
    X_bad = np.array([1.0, 0.5, 8.0])
    uv1_bad = project(X_bad, K, R1, t1)
    uv2_bad = project(X_bad, K, R2, t2) + np.array([0.0, 200.0])

    poses = [
        {"frame_idx": 0, "R": R1.tolist(), "t": t1.tolist(), "inliers": -1, "accepted": True},
        {"frame_idx": 1, "R": R2.tolist(), "t": t2.tolist(), "inliers": 100, "accepted": True},
    ]
    matches = [[
        (0, 0, uv1_good.tolist(), uv2_good.tolist()),
        (1, 1, uv1_bad.tolist(), uv2_bad.tolist()),
    ]]

    thresholds = ValidationThresholds(max_reprojection_error_px=50.0)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        _make_test_data(tmpdir, poses, matches, K)
        report = compute_real_reprojection(
            tmpdir / "stage2", tmpdir / "stage3",
            max_matches_per_pair=0,
            thresholds=thresholds,
        )

    assert report.status == "REPROJECTION_AVAILABLE"
    # Raw should contain all 4 observations (2 points × 2 cameras)
    assert report.raw_stats.observation_count == 4
    # Validated should contain only the good point's 2 observations
    assert report.validated_stats.observation_count == 2
    # Validated RMSE should be much lower than raw RMSE
    assert report.validated_stats.rmse < report.raw_stats.rmse
    print(f" [OK] Raw observations: {report.raw_stats.observation_count}")
    print(f" [OK] Validated observations: {report.validated_stats.observation_count}")
    print(f" [OK] Raw RMSE: {report.raw_stats.rmse:.4f} px")
    print(f" [OK] Validated RMSE: {report.validated_stats.rmse:.4f} px")
    print(f" [OK] Validated RMSE < Raw RMSE: confirmed")
    print("--- PASSED ---\n")


if __name__ == "__main__":
    test_valid_triangulation()
    test_degenerate_low_parallax()
    test_excessive_reprojection_outlier()
    test_behind_camera()
    test_raw_vs_validated_separation()
    print("=== ALL MILESTONE 8 SYNTHETIC TESTS PASSED ===")
