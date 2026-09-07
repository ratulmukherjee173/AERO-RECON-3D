import json
import numpy as np
from pathlib import Path
from typing import Dict, Any, Tuple
from .models import AlignmentReport

def _read_ply(path: Path) -> Tuple[np.ndarray, np.ndarray]:
    """
    Reads a binary little-endian PLY file containing xyz and rgb.
    """
    with open(path, "rb") as f:
        header = b""
        while b"end_header\n" not in header:
            header += f.readline()
            
    header_str = header.decode("ascii")
    lines = header_str.split("\n")
    vertex_count = 0
    for line in lines:
        if line.startswith("element vertex "):
            vertex_count = int(line.split()[-1])
            
    dt = np.dtype([
        ('x', 'f4'), ('y', 'f4'), ('z', 'f4'),
        ('red', 'u1'), ('green', 'u1'), ('blue', 'u1')
    ])
    
    data = np.fromfile(path, dtype=dt, count=vertex_count, offset=len(header))
    
    points = np.vstack((data['x'], data['y'], data['z'])).T
    colors = np.vstack((data['red'], data['green'], data['blue'])).T
    
    return points, colors

def _save_ply(path: Path, points: np.ndarray, colors: np.ndarray) -> None:
    """Write a binary little-endian PLY file with per-vertex RGB colour."""
    n = len(points)
    with open(path, "wb") as f:
        header = (
            "ply\n"
            "format binary_little_endian 1.0\n"
            f"element vertex {n}\n"
            "property float x\n"
            "property float y\n"
            "property float z\n"
            "property uchar red\n"
            "property uchar green\n"
            "property uchar blue\n"
            "end_header\n"
        )
        f.write(header.encode("ascii"))
        
        dt = np.dtype([
            ('x', 'f4'), ('y', 'f4'), ('z', 'f4'),
            ('red', 'u1'), ('green', 'u1'), ('blue', 'u1')
        ])
        
        data = np.empty(n, dtype=dt)
        data['x'] = points[:, 0].astype(np.float32)
        data['y'] = points[:, 1].astype(np.float32)
        data['z'] = points[:, 2].astype(np.float32)
        
        data['red'] = colors[:, 0].astype(np.uint8)
        data['green'] = colors[:, 1].astype(np.uint8)
        data['blue'] = colors[:, 2].astype(np.uint8)
        
        f.write(data.tobytes())

def transform_point_cloud(
    input_ply: Path,
    output_ply: Path,
    alignment_report: AlignmentReport,
    report_output: Path,
    job_id: str
) -> Dict[str, Any]:
    """
    Transforms a relative point cloud into a metric/georeferenced point cloud.
    X_metric = s R X_relative + t
    """
    # 1. Check Availability
    if alignment_report.alignment_status != "METRIC_ALIGNMENT_AVAILABLE" or \
       alignment_report.scale_status != "METRIC_SCALE_AVAILABLE" or \
       alignment_report.scale is None or \
       alignment_report.rotation is None or \
       alignment_report.translation is None:
           
        report = {
            "status": "METRIC_POINTCLOUD_UNAVAILABLE",
            "job_id": job_id,
            "source_point_cloud": str(input_ply.name),
            "output_point_cloud": None,
            "point_count_input": 0,
            "point_count_output": 0,
            "transform_direction": None,
            "scale": None,
            "scale_units": None,
            "rotation": None,
            "translation": None,
            "coordinate_system": None,
            "source_alignment_report": None,
            "reason": "Metric/georeferenced point cloud unavailable because the source video contains no GPS/IMU telemetry or external metric reference."
        }
        report_output.parent.mkdir(parents=True, exist_ok=True)
        with open(report_output, "w") as f:
            json.dump(report, f, indent=2)
        return report

    # 2. Extract Transform Data
    s = float(alignment_report.scale)
    R = np.array(alignment_report.rotation, dtype=np.float64)
    t = np.array(alignment_report.translation, dtype=np.float64).flatten()
    
    # 3. Validation Requirements
    if not np.isfinite(s) or np.isnan(s):
        report = _failed_report(job_id, input_ply, "Scale is nonfinite or NaN")
        _write_report(report_output, report)
        return report
        
    if s <= 0:
        report = _failed_report(job_id, input_ply, "Scale must be positive")
        _write_report(report_output, report)
        return report
        
    if R.shape != (3, 3) or not np.all(np.isfinite(R)):
        report = _failed_report(job_id, input_ply, "Rotation matrix must be 3x3 and finite")
        _write_report(report_output, report)
        return report
        
    if len(t) != 3 or not np.all(np.isfinite(t)):
        report = _failed_report(job_id, input_ply, "Translation vector must be size 3 and finite")
        _write_report(report_output, report)
        return report
        
    if abs(np.linalg.det(R) - 1.0) > 1e-3:
        report = _failed_report(job_id, input_ply, "Rotation determinant must be approximately +1")
        _write_report(report_output, report)
        return report
        
    if not np.allclose(R.T @ R, np.eye(3), atol=1e-3):
        report = _failed_report(job_id, input_ply, "Rotation matrix is not orthogonal")
        _write_report(report_output, report)
        return report
        
    if alignment_report.transform_direction != "X_metric = s R X_relative + T":
        report = _failed_report(job_id, input_ply, "Transform direction mismatch")
        _write_report(report_output, report)
        return report

    # 4. Read PLY
    try:
        points, colors = _read_ply(input_ply)
    except Exception as e:
        report = _failed_report(job_id, input_ply, f"Failed to read source PLY: {str(e)}")
        _write_report(report_output, report)
        return report
        
    in_count = len(points)
    if not np.all(np.isfinite(points)):
        report = _failed_report(job_id, input_ply, "Source point cloud contains nonfinite/NaN coordinates")
        _write_report(report_output, report)
        return report

    # 5. Transform: X_metric = s * R * X_relative + t
    # points is N x 3. We want R @ points.T (3xN), scaled, translated.
    points_transformed = s * (R @ points.T).T + t
    
    if not np.all(np.isfinite(points_transformed)):
        report = _failed_report(job_id, input_ply, "Transformed coordinates contain nonfinite/NaN values")
        _write_report(report_output, report)
        return report

    # 6. Save new PLY (Original is preserved as we output to a different path)
    output_ply.parent.mkdir(parents=True, exist_ok=True)
    _save_ply(output_ply, points_transformed, colors)
    
    out_count = len(points_transformed)
    if in_count != out_count:
        report = _failed_report(job_id, input_ply, "Point count mismatch after transformation")
        _write_report(report_output, report)
        return report
    
    # Generate Output Report
    # Note: Explicitly differentiate METRIC LOCAL ENU from global georeferencing
    coord_sys = alignment_report.coordinate_system
    if coord_sys == "ENU":
        coord_sys = "METRIC LOCAL ENU"

    report = {
        "status": "AVAILABLE",
        "job_id": job_id,
        "source_point_cloud": str(input_ply.name),
        "output_point_cloud": str(output_ply.name),
        "point_count_input": in_count,
        "point_count_output": out_count,
        "transform_direction": "X_metric = s R X_relative + T",
        "scale": s,
        "scale_units": "meters_per_relative_unit",
        "rotation": R.tolist(),
        "translation": t.tolist(),
        "coordinate_system": coord_sys,
        "source_alignment_report": str(report_output.parent / f"{Path(alignment_report.source_video).stem}_metric_alignment.json"),
        "reason": "Metric scaling applied."
    }
    
    _write_report(report_output, report)
    return report

def _failed_report(job_id: str, input_ply: Path, reason: str) -> Dict[str, Any]:
    return {
        "status": "FAILED",
        "job_id": job_id,
        "source_point_cloud": str(input_ply.name),
        "output_point_cloud": None,
        "point_count_input": 0,
        "point_count_output": 0,
        "transform_direction": None,
        "scale": None,
        "scale_units": None,
        "rotation": None,
        "translation": None,
        "coordinate_system": None,
        "source_alignment_report": None,
        "reason": reason
    }

def _write_report(report_output: Path, report: Dict[str, Any]) -> None:
    report_output.parent.mkdir(parents=True, exist_ok=True)
    with open(report_output, "w") as f:
        json.dump(report, f, indent=2)
