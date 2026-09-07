"""
SYNTHETIC MATHEMATICAL UNIT TEST

This test exclusively verifies the mathematical correctness of the 
Umeyama 3D similarity transformation algorithm. 
It does NOT represent real UAV accuracy.
"""

import numpy as np
import math
from app.trajectory.alignment import TrajectoryAligner

def test_umeyama():
    print("--- SYNTHETIC MATHEMATICAL UNIT TEST ---")
    
    # 1. Generate deterministic 3D source points
    np.random.seed(42)
    num_points = 100
    X_source = np.random.rand(3, num_points) * 10.0
    
    # 2. Define known transformation
    s_true = 2.5
    
    # Known rotation (e.g., 30 degrees around Z)
    theta = math.radians(30)
    c, s = math.cos(theta), math.sin(theta)
    R_true = np.array([
        [c, -s, 0],
        [s,  c, 0],
        [0,  0, 1]
    ])
    
    # Known translation
    t_true = np.array([[5.0], [-3.0], [1.5]])
    
    # 3. Generate target points: Y = s * R * X + t
    Y_target = s_true * R_true @ X_source + t_true
    
    # 4. Recover transform using our implementation
    s_est, R_est, t_est = TrajectoryAligner.umeyama(X_source, Y_target)
    
    # 5. Verify
    scale_error = abs(s_est - s_true)
    assert scale_error < 1e-5, f"Scale error too large: {scale_error}"
    print(f" [OK] Scale error: {scale_error:.2e} (Expected: 0)")
    
    rot_error = np.linalg.norm(R_est - R_true)
    assert rot_error < 1e-5, f"Rotation error too large: {rot_error}"
    print(f" [OK] Rotation error: {rot_error:.2e} (Expected: 0)")
    
    trans_error = np.linalg.norm(t_est - t_true)
    assert trans_error < 1e-5, f"Translation error too large: {trans_error}"
    print(f" [OK] Translation error: {trans_error:.2e} (Expected: 0)")
    
    # Verify determinant
    det_R = np.linalg.det(R_est)
    assert math.isclose(det_R, 1.0, abs_tol=1e-5), "Determinant of R is not 1.0"
    print(f" [OK] det(R): {det_R:.4f} (Expected: 1.0)")
    
    # Verify residual
    Y_est = s_est * R_est @ X_source + t_est
    residual = np.mean(np.linalg.norm(Y_est - Y_target, axis=0))
    assert residual < 1e-5, f"Residual too large: {residual}"
    print(f" [OK] Residual error: {residual:.2e} (Expected: 0)")
    
    print("--- MATHEMATICAL UNIT TEST PASSED ---\n")

if __name__ == "__main__":
    test_umeyama()
