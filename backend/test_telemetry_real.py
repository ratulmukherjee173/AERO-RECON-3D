import json
from pathlib import Path
from app.telemetry.extractor import TelemetryExtractor
from app.trajectory.models import CameraTrajectory
from app.trajectory.synchronizer import TelemetrySynchronizer

def test_real_telemetry():
    base_dir = Path(__file__).resolve().parent
    video_path = base_dir / "data" / "samples" / "drone_flight_01.mp4"
    out_path = base_dir / "data" / "outputs" / "telemetry" / "drone_flight_01_sync.json"
    
    print("--- REAL UAV TELEMETRY TEST ---")
    
    # 1. Extract telemetry
    extractor = TelemetryExtractor(str(video_path))
    telemetry_report = extractor.extract()
    
    # Verify no telemetry hallucinated
    assert telemetry_report.has_gps == False
    assert telemetry_report.has_imu == False
    assert len(telemetry_report.telemetry_samples) == 0
    print("[OK] Real UAV has no embedded telemetry.")
    
    # 2. Fake a CameraTrajectory to simulate Stage 3 output
    trajectory = CameraTrajectory(
        video_file="drone_flight_01.mp4",
        fps=30.0,
        frame_count=100,
        accepted_poses=100,
        points=[]
    )
    
    # 3. Synchronize
    synchronized_traj = TelemetrySynchronizer.synchronize(trajectory, telemetry_report)
    
    # Verify strict status separation
    assert synchronized_traj.gps_available == False
    assert synchronized_traj.gps_enu_available == False
    assert synchronized_traj.telemetry_sync_available == False
    assert synchronized_traj.camera_gps_correspondence_available == False
    assert synchronized_traj.metric_alignment_available == False
    print("[OK] Real UAV synchronized trajectory safely defaults to UNAVAILABLE statuses.")
    
    # 4. Save output
    out_path.parent.mkdir(parents=True, exist_ok=True)
    report_dict = {
        "GPS_AVAILABLE": synchronized_traj.gps_available,
        "GPS_ENU_AVAILABLE": synchronized_traj.gps_enu_available,
        "TELEMETRY_SYNC_AVAILABLE": synchronized_traj.telemetry_sync_available,
        "CAMERA_GPS_CORRESPONDENCE_AVAILABLE": synchronized_traj.camera_gps_correspondence_available,
        "METRIC_ALIGNMENT_AVAILABLE": synchronized_traj.metric_alignment_available,
        "status": "Telemetry unavailable in source video."
    }
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(report_dict, f, indent=2)
        
    print(f"[OK] Report written to {out_path}")
    print("--- REAL UAV TELEMETRY TEST PASSED ---")

if __name__ == "__main__":
    test_real_telemetry()
