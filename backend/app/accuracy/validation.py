from typing import List, Optional
from .models import (
    AccuracyReport, ReprojectionObservation, 
    ReferenceMeasurement, ReprojectionReport, MeasurementValidationReport
)
from .reprojection import calculate_reprojection_error
from .measurement import validate_measurements
import numpy as np

def generate_accuracy_report(
    reprojection_obs: List[ReprojectionObservation],
    camera_matrix: np.ndarray,
    rotation: np.ndarray,
    translation: np.ndarray,
    intrinsics_source: str = "ESTIMATED",
    reference_measurements: List[ReferenceMeasurement] = [],
    coordinate_system: str = "RELATIVE",
    metric_available: bool = False
) -> AccuracyReport:
    """
    Generates a full accuracy report encompassing reprojection and metric measurement validation.
    """
    report = AccuracyReport()
    
    # 1. Reprojection Error
    reproj_report = calculate_reprojection_error(
        reprojection_obs,
        camera_matrix,
        rotation,
        translation,
        intrinsics_source
    )
    report.reprojection = reproj_report
    
    # 2. Metric Measurement Error
    meas_report = validate_measurements(
        reference_measurements,
        coordinate_system,
        metric_available
    )
    report.metric_measurement = meas_report
    
    # 3. Geospatial Accuracy
    # (Placeholder for future milestones if WGS84 coordinates exist)
    report.geospatial_accuracy.status = "UNAVAILABLE"
    
    return report
