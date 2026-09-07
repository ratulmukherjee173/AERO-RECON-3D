from typing import Optional
from .models import CameraTrajectory, MetricReferenceTrajectory, AlignmentReport
from .alignment import TrajectoryAligner

class ScaleEstimator:
    """
    Foundation for estimating metric scale from various references (GPS, altitude, GCPs).
    """
    
    @staticmethod
    def estimate_scale(trajectory: CameraTrajectory, 
                       reference: Optional[MetricReferenceTrajectory] = None) -> AlignmentReport:
        """
        Estimates scale if a metric reference is provided.
        Returns an AlignmentReport object explicitly documenting the status.
        """
        report = AlignmentReport(
            source_video=trajectory.video_file,
        )
        
        if not reference or not reference.points:
            report.scale_status = "METRIC_SCALE_UNAVAILABLE"
            report.alignment_status = "METRIC_ALIGNMENT_UNAVAILABLE"
            report.reference_source = "UNAVAILABLE"
            trajectory.scale_status = "METRIC_SCALE_UNAVAILABLE"
            trajectory.metric = False
            return report
            
        report.reference_source = reference.source
            
        from .synchronizer import TelemetrySynchronizer
        import numpy as np
        
        matched_cam, matched_ref = TelemetrySynchronizer.match_points(trajectory, reference)
        
        if len(matched_cam) < 3:
            report.alignment_status = "METRIC_ALIGNMENT_UNAVAILABLE"
            report.scale_status = "METRIC_SCALE_UNAVAILABLE"
            return report
            
        X = np.array([pt.position for pt in matched_cam]).T
        Y = np.array([pt.position for pt in matched_ref]).T
        
        if not np.isfinite(X).all() or not np.isfinite(Y).all():
            report.scale_status = "METRIC_SCALE_UNAVAILABLE"
            report.alignment_status = "METRIC_ALIGNMENT_UNAVAILABLE"
            return report
            
        try:
            s, _, _ = TrajectoryAligner.umeyama(X, Y)
        except ValueError:
            report.scale_status = "METRIC_SCALE_UNAVAILABLE"
            report.alignment_status = "METRIC_ALIGNMENT_UNAVAILABLE"
            return report
            
        report.scale = float(s)
        report.scale_status = "METRIC_SCALE_AVAILABLE"
        report.scale_units = "meters_per_relative_unit"
        # Alignment is not fully performed/reported here, only scale
        report.alignment_status = "METRIC_ALIGNMENT_UNAVAILABLE"
        
        return report
