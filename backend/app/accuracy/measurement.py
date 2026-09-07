import numpy as np
import math
from typing import List
from .models import ReferenceMeasurement, MeasurementResult, MeasurementValidationReport

def validate_measurements(
    reference_measurements: List[ReferenceMeasurement],
    coordinate_system: str,
    metric_available: bool = False
) -> MeasurementValidationReport:
    """
    Validates reconstructed distance between points against reference ground truth.
    distance = ||P1 - P2||
    """
    report = MeasurementValidationReport(
        status="GROUND_TRUTH_UNAVAILABLE",
        units="meters" if metric_available else "relative_units",
        ground_truth_available=metric_available
    )
    
    if not metric_available or not reference_measurements:
        return report
        
    report.status = "MEASUREMENT_VALIDATION_AVAILABLE"
    
    errors = []
    rel_errors = []
    
    for ref in reference_measurements:
        if ref.known_distance <= 0:
            report.rejected_measurements += 1
            continue
            
        p1 = np.array(ref.point_a, dtype=np.float64)
        p2 = np.array(ref.point_b, dtype=np.float64)
        
        if not np.all(np.isfinite(p1)) or not np.all(np.isfinite(p2)):
            report.rejected_measurements += 1
            continue
            
        recon_dist = float(np.linalg.norm(p1 - p2))
        
        abs_err = abs(recon_dist - ref.known_distance)
        rel_err = abs_err / ref.known_distance
        pct_err = rel_err * 100.0
        
        res = MeasurementResult(
            measurement_id=ref.measurement_id,
            reconstructed_distance=recon_dist,
            absolute_error=abs_err,
            relative_error=rel_err,
            percentage_error=pct_err
        )
        report.results.append(res)
        report.valid_measurements += 1
        
        errors.append(abs_err)
        rel_errors.append(pct_err)
        
    if not errors:
        report.status = "MEASUREMENT_VALIDATION_UNAVAILABLE"
        return report
        
    errors_np = np.array(errors)
    pct_np = np.array(rel_errors)
    
    report.rmse = float(np.sqrt(np.mean(errors_np**2)))
    report.mae = float(np.mean(errors_np))
    report.median_error = float(np.median(errors_np))
    report.max_error = float(np.max(errors_np))
    report.min_error = float(np.min(errors_np))
    report.mean_percentage_error = float(np.mean(pct_np))
    report.max_percentage_error = float(np.max(pct_np))
    
    return report
