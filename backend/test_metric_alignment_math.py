import unittest
import numpy as np
from app.trajectory.alignment import TrajectoryAligner

class TestMetricAlignmentMath(unittest.TestCase):
    def setUp(self):
        # SYNTHETIC TEST DATA
        # Generate known relative coordinates
        self.X_relative = np.array([
            [0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
            [1.0, 1.0, 1.0]
        ]).T # 3xN
        
        self.scale = 2.5
        
        # 90 degrees around Z axis
        self.R = np.array([
            [0, -1, 0],
            [1,  0, 0],
            [0,  0, 1]
        ], dtype=float)
        
        self.t = np.array([[10.0], [20.0], [30.0]])
        
        # Forward transformation: X_metric = s R X_relative + t
        self.X_metric = self.scale * (self.R @ self.X_relative) + self.t
        
    def test_umeyama_recovery(self):
        s, R_est, t_est = TrajectoryAligner.umeyama(self.X_relative, self.X_metric)
        
        self.assertAlmostEqual(s, self.scale, places=6)
        np.testing.assert_allclose(R_est, self.R, atol=1e-6)
        np.testing.assert_allclose(t_est, self.t, atol=1e-6)
        
        # Verify R is proper rotation
        self.assertAlmostEqual(np.linalg.det(R_est), 1.0, places=6)
        np.testing.assert_allclose(R_est.T @ R_est, np.eye(3), atol=1e-6)
        
    def test_umeyama_reflection(self):
        # Induce a reflection in the metric data
        reflection = np.eye(3)
        reflection[2, 2] = -1
        X_metric_reflected = reflection @ self.X_metric
        
        # Umeyama should still recover a valid proper rotation (det=+1), 
        # though the fit will not be perfect because the points were reflected
        s, R_est, t_est = TrajectoryAligner.umeyama(self.X_relative, X_metric_reflected)
        
        self.assertAlmostEqual(np.linalg.det(R_est), 1.0, places=6)
        np.testing.assert_allclose(R_est.T @ R_est, np.eye(3), atol=1e-6)
        
    def test_umeyama_degenerate_variance(self):
        # All points the same
        X_degen = np.zeros((3, 5))
        Y_degen = np.zeros((3, 5))
        
        with self.assertRaises(ValueError):
            TrajectoryAligner.umeyama(X_degen, Y_degen)
            
    def test_umeyama_insufficient_points(self):
        X_few = self.X_relative[:, :2]
        Y_few = self.X_metric[:, :2]
        
        with self.assertRaises(ValueError):
            TrajectoryAligner.umeyama(X_few, Y_few)

if __name__ == "__main__":
    unittest.main()
