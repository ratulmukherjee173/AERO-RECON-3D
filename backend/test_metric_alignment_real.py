import argparse
import sys
import json
from pathlib import Path

from app.core.config import OUTPUTS_DIR, DATA_DIR
from app.trajectory.extractor import extract_trajectory
from app.trajectory.alignment import TrajectoryAligner
from app.trajectory.models import MetricReferenceTrajectory
from app.telemetry.extractor import TelemetryExtractor
from app.telemetry.models import GPSReferenceTrajectory
from app.trajectory.synchronizer import TelemetrySynchronizer
from app.trajectory.coordinates import ENUConverter

def run_real_test(job_id: str, video: str, fps: float):
    print("\n--- REAL UAV METRIC ALIGNMENT TEST (HONEST STATUS CHECK) ---")
    
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
    
    # Run sync to populate trajectory flags
    trajectory = TelemetrySynchronizer.synchronize(trajectory, telemetry_report)
    
    # Try alignment
    # Since drone_flight_01.mp4 has no valid GPS, reference will be empty.
    # In a full flow, we would convert telemetry to ENU and build MetricReferenceTrajectory.
    enu_pts, origin = ENUConverter.generate_enu_trajectory(telemetry_report.telemetry_samples)
    
    reference = MetricReferenceTrajectory(
        source="GPS_ENU",
        coordinate_system="ENU",
        units="meters",
        points=enu_pts
    ) if enu_pts else None
    
    print("Running metric alignment...")
    report = TrajectoryAligner.align_trajectory(trajectory, reference)
    
    # -------------------------------------------
    # VERIFY HONEST UNAVAILABLE DATA HANDLING
    # -------------------------------------------
    assert not trajectory.gps_available, "GPS_AVAILABLE should be false"
    assert not trajectory.gps_enu_available, "GPS_ENU_AVAILABLE should be false"
    assert not trajectory.telemetry_sync_available, "TELEMETRY_SYNC_AVAILABLE should be false"
    assert not trajectory.camera_gps_correspondence_available, "CAMERA_GPS_CORRESPONDENCE_AVAILABLE should be false"
    assert not trajectory.metric_alignment_available, "METRIC_ALIGNMENT_AVAILABLE should be false"
    
    assert report.scale_status == "METRIC_SCALE_UNAVAILABLE", "Scale status must be UNAVAILABLE"
    print(" [OK] Scale status correctly reports METRIC_SCALE_UNAVAILABLE")
    
    assert report.alignment_status == "METRIC_ALIGNMENT_UNAVAILABLE", "Alignment status must be UNAVAILABLE"
    print(" [OK] Alignment status correctly reports METRIC_ALIGNMENT_UNAVAILABLE")
    
    assert report.scale is None, "Scale factor must be None"
    print(" [OK] Scale factor is safely None")
    
    assert report.rotation is None, "Rotation must be None"
    print(" [OK] Rotation is safely None")
    
    assert report.translation is None, "Translation must be None"
    print(" [OK] Translation is safely None")
    
    print("--- REAL UAV TEST PASSED (HONESTY VERIFIED) ---\n")
    
    out_dir = DATA_DIR / "outputs" / "trajectory"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"{Path(video).stem}_metric_alignment.json"
    
    with open(out_file, "w") as f:
        json.dump(report.model_dump(), f, indent=2)

    print(f"Alignment JSON written to: {out_file}")

def main():
    parser = argparse.ArgumentParser(description="Test Metric Alignment (Milestone 12)")
    parser.add_argument("--job-id", type=str, required=True, help="Explicit Job ID to read camera_poses.json from")
    parser.add_argument("--video", type=str, default="drone_flight_01.mp4", help="Video file name")
    parser.add_argument("--fps", type=float, default=30.0, help="Video FPS")
    args = parser.parse_args()

    run_real_test(args.job_id, args.video, args.fps)

if __name__ == "__main__":
    main()
