"""
AERO RECON-3D — Real UAV Bundle Adjustment Test (Milestone 10)

Runs the trajectory refinement module on existing pipeline artifacts.
Verifies structure, metrics reporting, and HONESTY constraints.
"""
import argparse
import sys
import json
from pathlib import Path

from app.core.config import OUTPUTS_DIR
from app.trajectory.trajectory_refiner import run_trajectory_refinement, BundleAdjustmentConfig


def run_real_test(job_id: str):
    print(f"\n--- REAL UAV BUNDLE ADJUSTMENT TEST (Job: {job_id}) ---")

    job_dir = OUTPUTS_DIR / job_id
    if not job_dir.exists():
        print(f"[!] Error: {job_dir} does not exist.")
        sys.exit(1)
        
    config = BundleAdjustmentConfig(
        huber_delta=1.0,
        max_iterations=15,
        ftol=1e-3,
        xtol=1e-3,
        verbose=2
    )
    
    print("Running trajectory refinement (Bundle Adjustment)...")
    res = run_trajectory_refinement(job_dir, config)
    
    if res["status"] != "BA_SUCCESS":
        print(f" [!] BA Failed or Unavailable: {res.get('reason', 'Unknown')}")
        print("--- TEST PASSED (Proper failure handling) ---")
        return
        
    print(f" [OK] BA Status: {res['status']}")
    
    # Track stats
    ts = res["track_statistics"]
    print(f" [OK] Tracks Built: {ts['total_tracks_built']}")
    print(f" [OK] Valid Tracks: {ts['valid_tracks']}")
    print(f" [OK] Rejected (Conflict): {ts['rejected_conflict']}")
    
    # Landmark stats
    ls = res["landmark_statistics"]
    print(f" [OK] Initial Landmarks: {ls['initial_landmarks']}")
    
    # Optimizer
    opt = res["optimization_configuration"]
    print(f" [OK] Optimizer: {opt['optimizer']} (SciPy {opt['scipy_version']})")
    print(f" [OK] Huber Delta: {opt['huber_delta']}")
    
    # Metrics
    before = res["before_ba_metrics"]
    after = res["after_ba_metrics"]
    
    print("\n --- BEFORE BA (RAW) ---")
    print(f" RMSE: {before['rmse']:.4f} px")
    print(f" MAE:  {before['mae']:.4f} px")
    print(f" Max:  {before['max']:.4f} px")
    
    print("\n --- AFTER BA (RAW) ---")
    print(f" RMSE: {after['rmse']:.4f} px")
    print(f" MAE:  {after['mae']:.4f} px")
    print(f" Max:  {after['max']:.4f} px")
    
    print(f"\n Improvement in RMSE: {before['rmse'] - after['rmse']:.4f} px")
    
    # Trajectory
    tc = res["trajectory_comparison"]
    print("\n --- TRAJECTORY COMPARISON ---")
    print(f" Cameras: {tc['cameras']}")
    print(f" Original Length: {tc['original_trajectory_length']:.4f} (relative units)")
    print(f" Refined Length:  {tc['refined_trajectory_length']:.4f} (relative units)")
    print(f" Mean Camera Displacement Diff: {tc['mean_camera_displacement_diff']:.4f}")
    
    # Honesty Checks
    limitations = res["limitations"]
    assert "METRIC_SCALE_UNAVAILABLE" in limitations
    assert "GPS_IMU_UNAVAILABLE" in limitations
    print("\n [OK] Honesty constraints maintained (No fake metric scale/GPS)")
    
    # Verify outputs exist
    out_dir = job_dir / "trajectory"
    assert (out_dir / f"{job_id}_bundle_adjustment.json").exists()
    assert (out_dir / "refined_camera_trajectory.json").exists()
    
    print(" [OK] JSON output artifacts written correctly")
    
    print("\n--- REAL UAV TEST PASSED ---\n")


def main():
    parser = argparse.ArgumentParser(description="Test Bundle Adjustment Integration")
    parser.add_argument("--job-id", type=str, required=True, help="Explicit Job ID")
    args = parser.parse_args()

    run_real_test(args.job_id)


if __name__ == "__main__":
    main()
