import argparse
import sys
import json
from pathlib import Path

from app.core.config import OUTPUTS_DIR, DATA_DIR
from app.trajectory import extract_trajectory
from app.trajectory.scale import ScaleEstimator
from app.telemetry.extractor import TelemetryExtractor

def run_real_test(job_id: str, video: str, fps: float):
    print("\n--- REAL UAV TEST (HONEST STATUS CHECK) ---")
    
    job_dir = OUTPUTS_DIR / job_id
    poses_file = job_dir / "stage3" / "camera_poses.json"
    
    if not poses_file.exists():
        print(f"[!] Error: {poses_file} does not exist. Ensure the job ran stage3 successfully.")
        sys.exit(1)

    video_path = DATA_DIR / "samples" / video
    if not video_path.exists():
        print(f"[!] Error: Sample video {video_path} does not exist.")
        sys.exit(1)
        
    print(f"Extracting trajectory for Job {job_id}...")
    trajectory = extract_trajectory(poses_file, video, fps=fps)
    
    print("Extracting telemetry...")
    telemetry_extractor = TelemetryExtractor(str(video_path))
    telemetry_report = telemetry_extractor.extract()
    
    print("Estimating scale (without reference data)...")
    # In a real scenario with GPS, we would construct a MetricReferenceTrajectory here.
    # For drone_flight_01.mp4, we explicitly pass None to simulate lack of data.
    report = ScaleEstimator.estimate_scale(trajectory, reference=None)
    
    # -------------------------------------------
    # VERIFY HONEST UNAVAILABLE DATA HANDLING
    # -------------------------------------------
    assert report.scale_status == "METRIC_SCALE_UNAVAILABLE", "Scale status must be UNAVAILABLE"
    print(" [OK] Scale status correctly reports METRIC_SCALE_UNAVAILABLE")
    
    assert report.alignment_status == "METRIC_ALIGNMENT_UNAVAILABLE", "Alignment status must be METRIC_ALIGNMENT_UNAVAILABLE"
    print(" [OK] Alignment status correctly reports METRIC_ALIGNMENT_UNAVAILABLE")
    
    assert report.reference_source == "UNAVAILABLE", "Reference source must be UNAVAILABLE"
    print(" [OK] Reference source correctly reports UNAVAILABLE")
    
    assert report.metric is False, "Metric flag must be False"
    print(" [OK] Metric flag correctly reports False")
    
    assert report.georeferenced is False, "Georeferenced flag must be False"
    print(" [OK] Georeferenced flag correctly reports False")
    
    assert report.scale is None, "Scale factor must be None"
    print(" [OK] Scale factor is safely None")
    
    assert not telemetry_report.has_gps, "GPS must be unavailable for this sample"
    print(" [OK] GPS is accurately unavailable")
    
    assert not telemetry_report.has_imu, "IMU must be unavailable for this sample"
    print(" [OK] IMU is accurately unavailable")
    
    print("--- REAL UAV TEST PASSED (HONESTY VERIFIED) ---\n")
    
    out_dir = DATA_DIR / "outputs" / "trajectory"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"{Path(video).stem}_alignment.json"
    
    with open(out_file, "w") as f:
        json.dump(report.model_dump(), f, indent=2)

    print(f"Alignment JSON written to: {out_file}")

def main():
    parser = argparse.ArgumentParser(description="Test Alignment Extraction (Milestone 4)")
    parser.add_argument("--job-id", type=str, required=True, help="Explicit Job ID to read camera_poses.json from")
    parser.add_argument("--video", type=str, default="drone_flight_01.mp4", help="Video file name")
    parser.add_argument("--fps", type=float, default=30.0, help="Video FPS")
    args = parser.parse_args()

    run_real_test(args.job_id, args.video, args.fps)

if __name__ == "__main__":
    main()
