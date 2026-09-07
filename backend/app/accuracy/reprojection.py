import numpy as np
import math
from typing import List, Tuple, Dict, Any
from .models import ReprojectionObservation, ReprojectionReport

def calculate_reprojection_error(
    observations: List[ReprojectionObservation],
    camera_matrix: np.ndarray,
    rotation: np.ndarray,
    translation: np.ndarray,
    intrinsics_source: str = "ESTIMATED"
) -> ReprojectionReport:
    """
    Calculates reprojection error (in pixels).
    X_camera = R X_world + t
    u = fx * (x/z) + cx
    v = fy * (y/z) + cy
    """
    report = ReprojectionReport(
        camera_intrinsics_source=intrinsics_source,
        status="REPROJECTION_AVAILABLE"
    )
    
    if not observations:
        report.status = "REPROJECTION_UNAVAILABLE"
        return report
        
    if camera_matrix.shape != (3, 3) or not np.all(np.isfinite(camera_matrix)):
        report.status = "REPROJECTION_UNAVAILABLE"
        return report
        
    if rotation.shape != (3, 3) or not np.all(np.isfinite(rotation)):
        report.status = "REPROJECTION_UNAVAILABLE"
        return report
        
    # check det(R)
    det_R = np.linalg.det(rotation)
    if not math.isclose(det_R, 1.0, abs_tol=1e-3):
        report.status = "REPROJECTION_UNAVAILABLE"
        return report
        
    translation = translation.reshape(3, 1)
    if not np.all(np.isfinite(translation)):
        report.status = "REPROJECTION_UNAVAILABLE"
        return report
        
    fx = camera_matrix[0, 0]
    fy = camera_matrix[1, 1]
    cx = camera_matrix[0, 2]
    cy = camera_matrix[1, 2]
    
    errors = []
    
    for obs in observations:
        pt_3d = np.array(obs.point_3d, dtype=np.float64).reshape(3, 1)
        obs_2d = np.array(obs.observed_2d, dtype=np.float64)
        
        if not np.all(np.isfinite(pt_3d)) or not np.all(np.isfinite(obs_2d)):
            report.rejected_observations += 1
            continue
            
        # X_camera = R X_world + t
        x_cam = rotation @ pt_3d + translation
        z = x_cam[2, 0]
        
        # Check if point is behind camera
        if z <= 0:
            report.rejected_observations += 1
            continue
            
        x = x_cam[0, 0]
        y = x_cam[1, 0]
        
        u_proj = fx * (x / z) + cx
        v_proj = fy * (y / z) + cy
        
        err = math.sqrt((obs_2d[0] - u_proj)**2 + (obs_2d[1] - v_proj)**2)
        
        if not math.isfinite(err):
            report.rejected_observations += 1
            continue
            
        errors.append(err)
        report.valid_observations += 1
        
    if not errors:
        report.status = "REPROJECTION_UNAVAILABLE"
        return report
        
    errors_np = np.array(errors)
    report.rmse = float(np.sqrt(np.mean(errors_np**2)))
    report.mae = float(np.mean(errors_np))
    report.median = float(np.median(errors_np))
    report.max_error = float(np.max(errors_np))
    
    return report
