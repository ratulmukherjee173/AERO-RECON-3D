import argparse
import sys
import json
import math
import numpy as np
from pathlib import Path

from app.core.config import OUTPUTS_DIR, DATA_DIR
from app.trajectory import (
    extract_trajectory,
    TelemetrySynchronizer,
    ScaleEstimator,
    CameraTrajectory
)
from app.telemetry.extractor import TelemetryExtractor

def check_finite(val):
    if not isinstance(val, (int, float)):
        return False
    return math.isfinite(val)

def run_sanity_checks(trajectory: CameraTrajectory):
    print("\n--- Running Sanity Checks ---")
    
    # accepted pose count > 0
    assert trajectory.accepted_poses > 0, "Accepted pose count must be > 0"
    print(" [OK] Accepted pose count > 0")

    # finite XYZ coordinates, no NaN/Inf, valid 3x3 matrices, monotonically increasing
    last_frame = -1
    last_ts = -1.0
    
    for pt in trajectory.points:
        # Monotonicity
        assert pt.frame_index > last_frame, f"Frame indices not monotonic: {last_frame} -> {pt.frame_index}"
        assert pt.timestamp_seconds > last_ts, f"Timestamps not monotonic: {last_ts} -> {pt.timestamp_seconds}"
        last_frame = pt.frame_index
        last_ts = pt.timestamp_seconds
        
        # Finite position
        assert len(pt.position) == 3, "Position must have 3 elements"
        for val in pt.position:
            assert check_finite(val), f"Invalid position coordinate: {val}"
            
        # Rotation 3x3 and mathematical validity
        assert len(pt.orientation) == 3, "Orientation must have 3 rows"
        R_np = np.zeros((3, 3))
        for i, row in enumerate(pt.orientation):
            assert len(row) == 3, "Orientation must have 3 columns"
            for j, val in enumerate(row):
                assert check_finite(val), f"Invalid orientation value: {val}"
                R_np[i, j] = val
                
        # R.T @ R ≈ I
        I_approx = R_np.T @ R_np
        assert np.allclose(I_approx, np.eye(3), atol=1e-3), "Rotation matrix is not orthogonal"
        
        # det(R) ≈ 1
        det_R = np.linalg.det(R_np)
        assert math.isclose(det_R, 1.0, abs_tol=1e-3), f"Rotation determinant is {det_R}, expected 1.0"
                
    print(" [OK] Finite XYZ coordinates (no NaN/Inf)")
    print(" [OK] Valid 3x3 rotation matrices (orthogonal, det=1)")
    print(" [OK] Monotonically increasing frame indices")
    print(" [OK] Monotonically increasing timestamps")
    
    # correct FPS
    assert trajectory.fps > 0, "FPS must be > 0"
    print(" [OK] Correct FPS")
    
    # honest status flags
    assert trajectory.metric is False, "Metric scale must be False for this milestone"
    print(" [OK] Metric scale correctly reported as False")
    
    assert trajectory.georeferenced is False, "Georeferenced must be False for this milestone"
    print(" [OK] Georeferenced correctly reported as False")
    
    assert trajectory.gps_available is False, "GPS must be unavailable for current sample"
    print(" [OK] GPS unavailable correctly reported")
    
    assert trajectory.imu_available is False, "IMU must be unavailable for current sample"
    print(" [OK] IMU unavailable correctly reported")
    
    assert trajectory.scale_status == "METRIC_SCALE_UNAVAILABLE", "Scale status must be METRIC_SCALE_UNAVAILABLE"
    print(" [OK] Scale status correctly reported as UNAVAILABLE")
    
    assert trajectory.sync_status == "TELEMETRY_SYNC_UNAVAILABLE", "Sync status must be TELEMETRY_SYNC_UNAVAILABLE"
    print(" [OK] Sync status correctly reported as TELEMETRY_SYNC_UNAVAILABLE")
    
    print("--- Sanity Checks Passed ---\n")
    
    print("--- Trajectory Quality Stats (Relative Scale) ---")
    valid_points = [pt for pt in trajectory.points if pt.valid]
    print(f"Accepted poses: {trajectory.accepted_poses}")
    if valid_points:
        print(f"First camera position: {[round(x, 4) for x in valid_points[0].position]}")
        print(f"Last camera position: {[round(x, 4) for x in valid_points[-1].position]}")
        
        xs = [pt.position[0] for pt in valid_points]
        ys = [pt.position[1] for pt in valid_points]
        zs = [pt.position[2] for pt in valid_points]
        print(f"Min coordinates: [{round(min(xs), 4)}, {round(min(ys), 4)}, {round(min(zs), 4)}]")
        print(f"Max coordinates: [{round(max(xs), 4)}, {round(max(ys), 4)}, {round(max(zs), 4)}]")
        print(f"Bounding Box dimensions: [X: {round(max(xs)-min(xs), 4)}, Y: {round(max(ys)-min(ys), 4)}, Z: {round(max(zs)-min(zs), 4)}]")
        
        traj_length = 0.0
        for i in range(1, len(valid_points)):
            p1 = valid_points[i-1].position
            p2 = valid_points[i].position
            dist = math.sqrt(sum((p1[k]-p2[k])**2 for k in range(3)))
            traj_length += dist
        print(f"Total relative trajectory length: {round(traj_length, 4)}")
        
        det_list = [np.linalg.det(np.array(pt.orientation)) for pt in valid_points]
        print(f"Rotation determinant range: [{round(min(det_list), 6)}, {round(max(det_list), 6)}]")
        print(f"Invalid/NaN/Inf count: 0 (verified by sanity checks)")
    print("-------------------------------------------------\n")

def main():
    parser = argparse.ArgumentParser(description="Test Trajectory Extraction (Milestone 3)")
    parser.add_argument("--job-id", type=str, required=True, help="Explicit Job ID to read camera_poses.json from")
    parser.add_argument("--video", type=str, default="drone_flight_01.mp4", help="Video file name")
    parser.add_argument("--fps", type=float, default=30.0, help="Video FPS")
    args = parser.parse_args()

    job_dir = OUTPUTS_DIR / args.job_id
    poses_file = job_dir / "stage3" / "camera_poses.json"
    
    if not poses_file.exists():
        print(f"[!] Error: {poses_file} does not exist. Ensure the job ran stage3 successfully.")
        sys.exit(1)

    video_path = DATA_DIR / "samples" / args.video
    if not video_path.exists():
        print(f"[!] Error: Sample video {video_path} does not exist.")
        sys.exit(1)

    print(f"Extracting trajectory for Job {args.job_id}...")
    try:
        trajectory = extract_trajectory(poses_file, args.video, fps=args.fps)
    except Exception as e:
        print(f"[!] Extraction failed: {e}")
        sys.exit(1)

    print("Extracting telemetry (to test synchronization)...")
    telemetry_extractor = TelemetryExtractor(str(video_path))
    telemetry_report = telemetry_extractor.extract()

    print("Synchronizing telemetry with trajectory...")
    trajectory = TelemetrySynchronizer.synchronize(trajectory, telemetry_report)

    print("Estimating scale...")
    report = ScaleEstimator.estimate_scale(trajectory)

    run_sanity_checks(trajectory)

    out_dir = DATA_DIR / "outputs" / "trajectory"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"{Path(args.video).stem}_trajectory.json"
    
    with open(out_file, "w") as f:
        json.dump(trajectory.model_dump(), f, indent=2)

    print(f"Trajectory JSON written to: {out_file}")

if __name__ == "__main__":
    main()
