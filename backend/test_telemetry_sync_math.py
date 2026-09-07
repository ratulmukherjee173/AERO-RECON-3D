import unittest
import math
from app.telemetry.models import TelemetryReport, TelemetrySample, VideoInfo
from app.trajectory.models import CameraTrajectory, CameraTrajectoryPoint
from app.trajectory.synchronizer import TelemetrySynchronizer
from app.trajectory.coordinates import ENUConverter

class TestTelemetrySyncMath(unittest.TestCase):
    def setUp(self):
        self.video_info = VideoInfo(width=1920, height=1080, fps=30.0, frame_count=100, duration_sec=3.33)
        self.cam_pts = [
            CameraTrajectoryPoint(frame_index=0, timestamp_seconds=0.0, position=[0,0,0], orientation=[[1,0,0],[0,1,0],[0,0,1]], valid=True),
            CameraTrajectoryPoint(frame_index=1, timestamp_seconds=0.1, position=[1,0,0], orientation=[[1,0,0],[0,1,0],[0,0,1]], valid=True),
            CameraTrajectoryPoint(frame_index=2, timestamp_seconds=0.2, position=[2,0,0], orientation=[[1,0,0],[0,1,0],[0,0,1]], valid=True),
            CameraTrajectoryPoint(frame_index=3, timestamp_seconds=0.3, position=[3,0,0], orientation=[[1,0,0],[0,1,0],[0,0,1]], valid=True)
        ]
        self.trajectory = CameraTrajectory(
            video_file="synthetic.mp4",
            fps=30.0,
            frame_count=4,
            accepted_poses=4,
            points=self.cam_pts
        )

    def test_nearest_neighbour_matching(self):
        samples = [
            TelemetrySample(timestamp=0.01, source="synthetic"),
            TelemetrySample(timestamp=0.12, source="synthetic"),
            TelemetrySample(timestamp=0.25, source="synthetic"), # Not perfectly matching 0.2
            TelemetrySample(timestamp=0.29, source="synthetic")  # Matches 0.3
        ]
        report = TelemetryReport(source_file="synthetic.mp4", video_info=self.video_info, telemetry_samples=samples)
        
        result = TelemetrySynchronizer.synchronize(self.trajectory, report, max_time_diff=0.06)
        
        self.assertTrue(result.telemetry_sync_available)
        self.assertEqual(report.sync_report.matched_samples, 4)
        
    def test_excessive_offset_rejection(self):
        samples = [
            TelemetrySample(timestamp=0.5, source="synthetic"),
            TelemetrySample(timestamp=0.6, source="synthetic"),
            TelemetrySample(timestamp=0.7, source="synthetic"),
            TelemetrySample(timestamp=0.8, source="synthetic")
        ]
        report = TelemetryReport(source_file="synthetic.mp4", video_info=self.video_info, telemetry_samples=samples)
        
        result = TelemetrySynchronizer.synchronize(self.trajectory, report, max_time_diff=0.1)
        
        self.assertFalse(result.telemetry_sync_available)
        self.assertEqual(report.sync_report.status, "TELEMETRY_SYNC_UNAVAILABLE")

    def test_enu_conversion(self):
        # Known WGS84 to ENU conversion test
        # New York roughly 40.7128, -74.0060, alt 10
        samples = [
            TelemetrySample(timestamp=0.0, latitude=40.7128, longitude=-74.0060, altitude=10.0, source="synthetic"),
            TelemetrySample(timestamp=0.1, latitude=40.7129, longitude=-74.0060, altitude=10.0, source="synthetic")
        ]
        
        enu_pts, origin = ENUConverter.generate_enu_trajectory(samples)
        self.assertEqual(len(enu_pts), 2)
        
        self.assertAlmostEqual(enu_pts[0].position[0], 0.0, places=4)
        self.assertAlmostEqual(enu_pts[0].position[1], 0.0, places=4)
        self.assertAlmostEqual(enu_pts[0].position[2], 0.0, places=4)
        
        # Moving North (increasing latitude)
        self.assertTrue(enu_pts[1].position[1] > 0.0) # North should be positive
        self.assertAlmostEqual(enu_pts[1].position[0], 0.0, places=2) # East should be ~0
        
    def test_invalid_lat_lon(self):
        samples = [
            TelemetrySample(timestamp=0.0, latitude=None, longitude=-74.0060, altitude=10.0, source="synthetic")
        ]
        enu_pts, origin = ENUConverter.generate_enu_trajectory(samples)
        self.assertEqual(len(enu_pts), 0)
        self.assertIsNone(origin)

if __name__ == '__main__':
    unittest.main()
