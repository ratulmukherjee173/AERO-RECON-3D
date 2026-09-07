"""
SYNTHETIC MATHEMATICAL UNIT TEST

This test exclusively verifies the mathematical correctness of the 
measurement error calculation (RMSE/MAE/percentage error).
It does NOT represent real UAV accuracy.
"""

import math
from app.accuracy import validate_measurements, ReferenceMeasurement

def test_measurement_validation():
    print("--- SYNTHETIC MEASUREMENT UNIT TEST ---")
    
    # 1. Known reference measurement
    # Ground truth distance: 10.0 meters
    ref = ReferenceMeasurement(
        measurement_id="test_01",
        description="Synthetic Test Distance",
        point_a=[0.0, 0.0, 0.0],
        point_b=[10.0, 0.0, 0.0],
        known_distance=10.0,
        units="meters",
        source="SYNTHETIC_GROUND_TRUTH"
    )
    
    # 2. Known reconstruction (intentionally perturbed)
    # Reconstructed distance: sqrt(9.82^2) = 9.82 meters
    # We simulate this by changing the reconstructed point_b coordinates slightly.
    # Actually, validate_measurements receives the reconstructed coordinates via point_a and point_b!
    # Wait, ReferenceMeasurement receives point_a and point_b as RECONSTRUCTED points, and known_distance as the GROUND TRUTH distance.
    ref.point_a = [0.0, 0.0, 0.0]
    ref.point_b = [9.82, 0.0, 0.0]  # This makes the reconstructed Euclidean distance 9.82
    
    # Expected Error:
    # Absolute error: |9.82 - 10.0| = 0.18 meters
    # Percentage error: (0.18 / 10.0) * 100 = 1.8%
    
    # 3. Run validation
    report = validate_measurements([ref], coordinate_system="METRIC_LOCAL", metric_available=True)
    
    # 4. Verify
    assert report.status == "MEASUREMENT_VALIDATION_AVAILABLE"
    assert report.valid_measurements == 1
    
    abs_err = report.mae
    pct_err = report.mean_percentage_error
    
    assert math.isclose(abs_err, 0.18, abs_tol=1e-5), f"Expected MAE 0.18, got {abs_err}"
    print(f" [OK] Absolute error correctly calculated: {abs_err:.2f} meters (Expected: 0.18)")
    
    assert math.isclose(pct_err, 1.8, abs_tol=1e-5), f"Expected percentage error 1.8%, got {pct_err}"
    print(f" [OK] Percentage error correctly calculated: {pct_err:.2f}% (Expected: 1.8%)")
    
    print("--- MATHEMATICAL MEASUREMENT TEST PASSED ---\n")

if __name__ == "__main__":
    test_measurement_validation()
