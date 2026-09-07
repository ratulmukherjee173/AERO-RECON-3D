"""
SYNTHETIC MATHEMATICAL UNIT TEST

This test exclusively verifies the mathematical correctness of the 
reprojection error calculation algorithm (pixels). 
It does NOT represent real UAV accuracy.
"""
import numpy as np
import math
from app.accuracy import calculate_reprojection_error, ReprojectionObservation

def test_reprojection_error():
    print("--- SYNTHETIC REPROJECTION UNIT TEST ---")
    
    # 1. Known Intrinsic Camera Matrix
    fx, fy = 1000.0, 1000.0
    cx, cy = 960.0, 540.0
    K = np.array([
        [fx,  0, cx],
        [ 0, fy, cy],
        [ 0,  0,  1]
    ])
    
    # 2. Known Extrinsic Pose (Identity Rotation, no Translation for simplicity)
    R = np.eye(3)
    t = np.array([0.0, 0.0, 0.0])
    
    # 3. Known 3D Point (In front of camera)
    X = np.array([5.0, 3.0, 10.0])
    
    # Expected projection:
    # X_cam = R*X + t = [5, 3, 10]
    # u = fx * 5/10 + cx = 1000 * 0.5 + 960 = 1460
    # v = fy * 3/10 + cy = 1000 * 0.3 + 540 = 840
    
    expected_u, expected_v = 1460.0, 840.0
    
    # Intentionally perturb the observation by exactly 3 pixels horizontally and 4 vertically.
    # Total error = sqrt(3^2 + 4^2) = 5.0 pixels
    obs = ReprojectionObservation(
        point_3d=X.tolist(),
        observed_2d=[expected_u + 3.0, expected_v + 4.0]
    )
    
    # 4. Run calculation
    report = calculate_reprojection_error([obs], K, R, t)
    
    # 5. Verify
    assert report.status == "REPROJECTION_AVAILABLE"
    assert report.valid_observations == 1
    assert report.rejected_observations == 0
    assert report.units == "pixels"
    
    assert math.isclose(report.rmse, 5.0, abs_tol=1e-5), f"Expected RMSE 5.0, got {report.rmse}"
    print(f" [OK] RMSE properly calculated: {report.rmse:.2f} pixels (Expected: 5.00)")
    
    assert math.isclose(report.mae, 5.0, abs_tol=1e-5)
    print(f" [OK] MAE properly calculated: {report.mae:.2f} pixels (Expected: 5.00)")
    
    print("--- MATHEMATICAL REPROJECTION TEST PASSED ---\n")

if __name__ == "__main__":
    test_reprojection_error()
