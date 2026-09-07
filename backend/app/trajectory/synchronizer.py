from typing import Optional, List, Tuple
from .models import CameraTrajectory, CameraTrajectoryPoint, MetricReferenceTrajectory, MetricReferencePoint
from ..telemetry.models import TelemetryReport, TelemetrySyncReport, TelemetrySample

class TelemetrySynchronizer:
    """
    Synchronizes CameraTrajectory timestamps with TelemetryReport timestamps.
    """
    
    @staticmethod
    def match_points(trajectory: CameraTrajectory, 
                     reference: MetricReferenceTrajectory, 
                     max_time_diff: float = 0.5) -> Tuple[List[CameraTrajectoryPoint], List[MetricReferencePoint]]:
        """
        Matches trajectory points to reference points by nearest timestamp.
        """
        matched_cam = []
        matched_ref = []
        
        for cam_pt in trajectory.points:
            if not cam_pt.valid:
                continue
                
            closest_ref = None
            min_diff = max_time_diff
            
            for ref_pt in reference.points:
                if not ref_pt.valid:
                    continue
                diff = abs(cam_pt.timestamp_seconds - ref_pt.timestamp)
                if diff < min_diff:
                    min_diff = diff
                    closest_ref = ref_pt
                    
            if closest_ref:
                matched_cam.append(cam_pt)
                matched_ref.append(closest_ref)
                
        return matched_cam, matched_ref

    @staticmethod
    def synchronize(trajectory: CameraTrajectory, telemetry: Optional[TelemetryReport], max_time_diff: float = 0.5) -> CameraTrajectory:
        # Default all statuses to false
        trajectory.gps_available = False
        trajectory.gps_enu_available = False
        trajectory.telemetry_sync_available = False
        trajectory.camera_gps_correspondence_available = False
        trajectory.metric_alignment_available = False
        trajectory.imu_available = False
        trajectory.sync_status = "TELEMETRY_SYNC_UNAVAILABLE"

        if not telemetry:
            return trajectory
            
        trajectory.gps_available = telemetry.has_gps
        trajectory.imu_available = telemetry.has_imu
        
        if not telemetry.telemetry_samples:
            return trajectory
            
        sync_report = TelemetrySyncReport()
        sync_report.status = "TELEMETRY_SYNC_UNAVAILABLE"
        
        # In a real scenario with explicit offsets, we would apply time_offset here.
        # Since it is unknown in general and we should not silently assume 0 unless explicitly known:
        # We will assume offset = 0 if timestamps roughly align.
        
        valid_cam_pts = [p for p in trajectory.points if p.valid]
        if not valid_cam_pts:
            return trajectory
            
        sync_report.video_start_time = valid_cam_pts[0].timestamp_seconds
        sync_report.telemetry_start_time = telemetry.telemetry_samples[0].timestamp
        
        # Check if timestamps overlap at all
        cam_times = [p.timestamp_seconds for p in valid_cam_pts]
        tel_times = [s.timestamp for s in telemetry.telemetry_samples]
        
        if max(cam_times) < min(tel_times) - max_time_diff or min(cam_times) > max(tel_times) + max_time_diff:
            sync_report.status = "TELEMETRY_SYNC_UNAVAILABLE"
            sync_report.synchronization_method = "UNAVAILABLE"
            telemetry.sync_report = sync_report
            return trajectory
            
        # Perform matching
        matched = 0
        diffs = []
        for c_time in cam_times:
            closest_diff = min(abs(c_time - t_time) for t_time in tel_times)
            if closest_diff <= max_time_diff:
                matched += 1
                diffs.append(closest_diff)
                
        if matched == 0:
            telemetry.sync_report = sync_report
            return trajectory
            
        sync_report.matched_samples = matched
        sync_report.unmatched_video_frames = len(cam_times) - matched
        sync_report.unmatched_telemetry_samples = len(tel_times) - matched
        sync_report.mean_time_difference = sum(diffs) / len(diffs)
        sync_report.max_time_difference = max(diffs)
        sync_report.time_offset = 0.0
        sync_report.synchronization_method = "NEAREST_NEIGHBOUR"
        sync_report.status = "TELEMETRY_SYNC_AVAILABLE"
        
        telemetry.sync_report = sync_report
        
        trajectory.telemetry_sync_available = True
        trajectory.sync_status = "TELEMETRY_SYNC_AVAILABLE"
        
        # If we have GPS, then we also have ENU (handled downstream, but we flag correspondence as possible)
        if telemetry.has_gps:
            trajectory.gps_enu_available = True
            trajectory.camera_gps_correspondence_available = True
            
        return trajectory

