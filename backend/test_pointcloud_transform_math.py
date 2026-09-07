"""
SYNTHETIC MATHEMATICAL UNIT TEST

This test exclusively verifies the mathematical correctness of the 
Point Cloud Transformation algorithm (X_target = s R X_source + t). 
It does NOT represent real UAV accuracy.
"""

import math
import numpy as np
from pathlib import Path
from app.trajectory.models import AlignmentReport
from app.trajectory.pointcloud_transform import _save_ply, _read_ply, transform_point_cloud
import tempfile
import os

def test_pointcloud_transform():
    print("--- SYNTHETIC POINT CLOUD TRANSFORM TEST ---")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        input_ply = tmpdir_path / "input.ply"
        output_ply = tmpdir_path / "output.ply"
        report_json = tmpdir_path / "report.json"
        
        # 1. Generate synthetic points & colors
        np.random.seed(42)
        n_points = 500
        points = np.random.rand(n_points, 3).astype(np.float32) * 10.0
        colors = np.random.randint(0, 256, (n_points, 3), dtype=np.uint8)
        
        # Save synthetic PLY
        _save_ply(input_ply, points, colors)
        
        # 2. Define known transformation
        s_true = 3.0
        theta = math.radians(45)
        c, s = math.cos(theta), math.sin(theta)
        R_true = np.array([
            [c, -s, 0],
            [s,  c, 0],
            [0,  0, 1]
        ])
        t_true = np.array([10.0, -5.0, 2.5])
        
        # Create AlignmentReport
        report = AlignmentReport(
            source_video="synthetic",
            alignment_status="METRIC_ALIGNMENT_AVAILABLE",
            scale_status="METRIC_SCALE_AVAILABLE",
            scale=s_true,
            rotation=R_true.tolist(),
            translation=t_true.tolist(),
            coordinate_system="METRIC_LOCAL",
            units="meters",
            metric=True,
            georeferenced=False,
            transform_direction="X_metric = s R X_relative + T"
        )
        
        # 3. Transform
        result_report = transform_point_cloud(input_ply, output_ply, report, report_json, job_id="test_m5_math")
        
        # 4. Verify report
        assert result_report["status"] == "AVAILABLE"
        assert result_report["point_count_input"] == n_points
        assert result_report["point_count_output"] == n_points
        
        # 5. Verify PLY contents mathematically
        assert output_ply.exists()
        out_pts, out_cols = _read_ply(output_ply)
        
        assert len(out_pts) == n_points
        
        # Verify RGB is preserved exactly
        assert np.array_equal(colors, out_cols), "RGB values were modified"
        print(" [OK] RGB values preserved perfectly")
        
        # Calculate expected XYZ
        expected_pts = s_true * (R_true @ points.T).T + t_true
        
        # Verify XYZ
        residual = np.max(np.abs(out_pts - expected_pts))
        assert residual < 1e-4, f"XYZ transformation residual too large: {residual}"
        print(f" [OK] Transformation mathematically correct (Residual: {residual:.2e})")
        print(f" [OK] Scale applied: {s_true}")
        detR = np.linalg.det(np.array(result_report['rotation']))
        print(f" [OK] Rotation determinant: {detR:.4f}")
        
    print("--- MATHEMATICAL TRANSFORM TEST PASSED ---\n")

if __name__ == "__main__":
    test_pointcloud_transform()
