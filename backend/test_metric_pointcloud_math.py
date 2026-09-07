import unittest
import numpy as np
import os
from pathlib import Path
import tempfile
import json
import uuid

from app.trajectory.pointcloud_transform import _save_ply, _read_ply, transform_point_cloud
from app.trajectory.models import AlignmentReport

class TestMetricPointCloudMath(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for tests
        self.test_dir = Path(tempfile.mkdtemp())
        
        self.job_id = f"test_{uuid.uuid4().hex[:8]}"
        self.input_ply = self.test_dir / "input.ply"
        self.output_ply = self.test_dir / "output_metric.ply"
        self.report_output = self.test_dir / "report.json"
        
        # 1. Generate deterministic point cloud
        self.points = np.array([
            [0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
            [1.0, 2.0, 3.0]
        ], dtype=np.float32)
        
        self.colors = np.array([
            [255, 0, 0],
            [0, 255, 0],
            [0, 0, 255],
            [255, 255, 0],
            [128, 128, 128]
        ], dtype=np.uint8)
        
        _save_ply(self.input_ply, self.points, self.colors)
        
        # 2. Known Transformation
        self.scale = 2.5
        # 90 degrees around Z axis
        self.R = np.array([
            [0, -1, 0],
            [1,  0, 0],
            [0,  0, 1]
        ], dtype=np.float64)
        self.t = np.array([10.0, 20.0, 30.0], dtype=np.float64)
        
        # 3. Expected Output
        self.expected_points = self.scale * (self.R @ self.points.T).T + self.t
        
        # Base Alignment Report
        self.base_report = AlignmentReport(
            source_video="test.mp4",
            scale_status="METRIC_SCALE_AVAILABLE",
            alignment_status="METRIC_ALIGNMENT_AVAILABLE",
            scale=self.scale,
            rotation=self.R.tolist(),
            translation=self.t.tolist(),
            transform_direction="X_metric = s R X_relative + T",
            coordinate_system="ENU"
        )
        
    def tearDown(self):
        # Cleanup
        for p in [self.input_ply, self.output_ply, self.report_output]:
            if p.exists():
                p.unlink()
        os.rmdir(self.test_dir)

    def test_valid_transformation(self):
        report = transform_point_cloud(
            self.input_ply, self.output_ply, self.base_report, self.report_output, self.job_id
        )
        
        self.assertEqual(report["status"], "AVAILABLE")
        self.assertTrue(self.output_ply.exists())
        self.assertEqual(report["coordinate_system"], "METRIC LOCAL ENU")
        
        out_pts, out_cols = _read_ply(self.output_ply)
        
        # 1. Output XYZ matches expected
        np.testing.assert_allclose(out_pts, self.expected_points, atol=1e-5)
        
        # 2. RGB exactly preserved
        np.testing.assert_array_equal(out_cols, self.colors)
        
        # 3. Point count preserved
        self.assertEqual(len(out_pts), len(self.points))
        self.assertEqual(report["point_count_input"], len(self.points))
        self.assertEqual(report["point_count_output"], len(self.points))

    def test_invalid_scale(self):
        for bad_scale in [-1.0, 0.0, np.nan, np.inf]:
            self.base_report.scale = bad_scale
            report = transform_point_cloud(
                self.input_ply, self.output_ply, self.base_report, self.report_output, self.job_id
            )
            self.assertEqual(report["status"], "FAILED")
            self.assertFalse(self.output_ply.exists())

    def test_reflection_matrix_rejected(self):
        # det(R) = -1
        reflection_R = np.eye(3)
        reflection_R[2, 2] = -1
        self.base_report.rotation = reflection_R.tolist()
        
        report = transform_point_cloud(
            self.input_ply, self.output_ply, self.base_report, self.report_output, self.job_id
        )
        self.assertEqual(report["status"], "FAILED")
        self.assertIn("determinant", report["reason"])

    def test_missing_alignment(self):
        self.base_report.alignment_status = "METRIC_ALIGNMENT_UNAVAILABLE"
        report = transform_point_cloud(
            self.input_ply, self.output_ply, self.base_report, self.report_output, self.job_id
        )
        self.assertEqual(report["status"], "METRIC_POINTCLOUD_UNAVAILABLE")
        self.assertIsNone(report["scale"])
        self.assertFalse(self.output_ply.exists())
        
    def test_invalid_transform_direction(self):
        self.base_report.transform_direction = "X_relative = s R X_metric + T"
        report = transform_point_cloud(
            self.input_ply, self.output_ply, self.base_report, self.report_output, self.job_id
        )
        self.assertEqual(report["status"], "FAILED")
        self.assertIn("Transform direction mismatch", report["reason"])

if __name__ == "__main__":
    unittest.main()
