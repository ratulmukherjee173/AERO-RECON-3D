from typing import Optional, Tuple
import numpy as np

from .models import CameraTrajectory, RigidTransform, AlignmentReport

class TrajectoryAligner:
    """
    Foundation for aligning a relative camera trajectory to a global coordinate frame (e.g., GPS).
    Implements 3D Umeyama similarity transformation.
    """
    
    @staticmethod
    def umeyama(X: np.ndarray, Y: np.ndarray) -> Tuple[float, np.ndarray, np.ndarray]:
        """
        Estimates the similarity transformation (s, R, t) that maps point set X to Y.
        Y = s * R * X + t
        
        Args:
            X: 3xN numpy array of source points (relative trajectory)
            Y: 3xN numpy array of target points (metric reference)
            
        Returns:
            s: float, scale factor
            R: 3x3 rotation matrix
            t: 3x1 translation vector
        """
        assert X.shape == Y.shape, "Point sets must have same shape"
        m, n = X.shape
        assert m == 3, "Points must be 3D"
        
        if n < 3:
            raise ValueError("At least 3 points required for 3D alignment")
            
        # Centroids
        mean_X = np.mean(X, axis=1, keepdims=True)
        mean_Y = np.mean(Y, axis=1, keepdims=True)
        
        X_centered = X - mean_X
        Y_centered = Y - mean_Y
        
        # Variances
        var_X = np.sum(X_centered**2) / n
        if var_X < 1e-8:
            raise ValueError("Source point set has zero variance (degenerate)")
            
        var_Y = np.sum(Y_centered**2) / n
        if var_Y < 1e-8:
            raise ValueError("Target point set has zero variance (degenerate)")
            
        # Covariance matrix
        Sigma = (Y_centered @ X_centered.T) / n
        
        # SVD
        U, D, Vt = np.linalg.svd(Sigma)
        
        # Rotation
        R = U @ Vt
        
        # Handle reflection (ensure det(R) = +1)
        if np.linalg.det(R) < 0:
            S = np.eye(3)
            S[2, 2] = -1
            R = U @ S @ Vt
            D[-1] = -D[-1]
            
        # Scale
        s = np.sum(D) / var_X
        if s <= 1e-8 or not np.isfinite(s):
            raise ValueError("Estimated scale is invalid/non-positive")
            
        # Translation
        t = mean_Y - s * R @ mean_X
        
        return float(s), R, t

    @staticmethod
    def align_trajectory(trajectory: CameraTrajectory, reference: Optional['MetricReferenceTrajectory']) -> AlignmentReport:
        from .models import AlignmentErrorStats
        from .synchronizer import TelemetrySynchronizer
        
        report = AlignmentReport(source_video=trajectory.video_file)
        
        if not reference or not reference.points:
            report.scale_status = "METRIC_SCALE_UNAVAILABLE"
            report.alignment_status = "METRIC_ALIGNMENT_UNAVAILABLE"
            report.reference_source = "UNAVAILABLE"
            return report
            
        report.reference_source = reference.source
            
        matched_cam, matched_ref = TelemetrySynchronizer.match_points(trajectory, reference)
        
        if len(matched_cam) < 3:
            report.scale_status = "METRIC_SCALE_UNAVAILABLE"
            report.alignment_status = "METRIC_ALIGNMENT_UNAVAILABLE"
            report.warnings.append("Insufficient matched points (<3) for 7-DoF alignment.")
            return report
            
        X = np.array([pt.position for pt in matched_cam]).T  # 3xN
        Y = np.array([pt.position for pt in matched_ref]).T  # 3xN
        
        # Sanity check for nonfinite values
        if not np.isfinite(X).all() or not np.isfinite(Y).all():
            report.scale_status = "METRIC_SCALE_UNAVAILABLE"
            report.alignment_status = "METRIC_ALIGNMENT_UNAVAILABLE"
            report.warnings.append("Nonfinite coordinates in matched trajectories.")
            return report
            
        try:
            s, R, t = TrajectoryAligner.umeyama(X, Y)
        except ValueError as e:
            report.scale_status = "METRIC_SCALE_UNAVAILABLE"
            report.alignment_status = "METRIC_ALIGNMENT_UNAVAILABLE"
            report.warnings.append(f"Umeyama alignment failed: {str(e)}")
            return report
            
        report.scale = float(s)
        report.rotation = R.tolist()
        report.translation = t.flatten().tolist()
        report.transform_direction = "X_metric = s R X_relative + T"
        report.scale_units = "meters_per_relative_unit"
        report.error_units = "meters"
        report.coordinate_system = reference.coordinate_system
        report.matched_point_count = len(matched_cam)
        
        report.scale_status = "METRIC_SCALE_AVAILABLE"
        report.alignment_status = "METRIC_ALIGNMENT_AVAILABLE"
        report.metric = True
        trajectory.metric = True
        trajectory.scale_status = "METRIC_SCALE_AVAILABLE"
        trajectory.metric_alignment_available = True
        
        # Errors
        def compute_stats(X_aligned: np.ndarray, Y_target: np.ndarray) -> AlignmentErrorStats:
            errors = np.linalg.norm(X_aligned - Y_target, axis=0)
            return AlignmentErrorStats(
                rmse=float(np.sqrt(np.mean(errors**2))),
                mae=float(np.mean(errors)),
                median=float(np.median(errors)),
                p95=float(np.percentile(errors, 95)),
                p99=float(np.percentile(errors, 99)),
                max=float(np.max(errors))
            )

        # Before alignment
        report.before_alignment_errors = compute_stats(X, Y)
        
        # After alignment
        X_aligned = s * (R @ X) + t
        report.after_alignment_errors = compute_stats(X_aligned, Y)
        
        return report
