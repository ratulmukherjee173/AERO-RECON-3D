import argparse
import sys
import json
import shutil
from pathlib import Path

from app.core.config import OUTPUTS_DIR, DATA_DIR
from app.trajectory.models import AlignmentReport
from app.trajectory.pointcloud_transform import transform_point_cloud

def run_real_test(job_id: str):
    print("\n--- REAL UAV POINT CLOUD TEST (HONEST STATUS CHECK) ---")
    
    job_dir = OUTPUTS_DIR / job_id
    input_ply = job_dir / "stage5" / "point_cloud.ply"
    output_ply = job_dir / "stage5" / "metric_point_cloud.ply"
    report_json = job_dir / "stage5" / "point_cloud_transformation_report.json"
    
    if not input_ply.exists():
        print(f"[!] Error: {input_ply} does not exist.")
        sys.exit(1)

    print(f"Loading alignment report for Job {job_id}...")
    alignment_file = DATA_DIR / "outputs" / "trajectory" / "drone_flight_01_alignment.json"
    
    if not alignment_file.exists():
        print(f"[!] Error: {alignment_file} does not exist. Run test_alignment_real.py first.")
        sys.exit(1)
        
    with open(alignment_file, "r") as f:
        alignment_data = json.load(f)
        report = AlignmentReport(**alignment_data)

    print("Attempting to transform point cloud...")
    
    # Store original file stats
    orig_size = input_ply.stat().st_size
    
    result = transform_point_cloud(input_ply, output_ply, report, report_json, job_id=job_id)
    
    # -------------------------------------------
    # VERIFY HONEST UNAVAILABLE DATA HANDLING
    # -------------------------------------------
    assert result["status"] == "METRIC_POINTCLOUD_UNAVAILABLE", "Status must be UNAVAILABLE"
    print(" [OK] Status correctly reports UNAVAILABLE")
    
    assert not output_ply.exists(), "Metric PLY must not be created when alignment is unavailable"
    print(" [OK] No fake metric PLY generated")
    
    assert report_json.exists(), "Transformation report JSON must be written"
    print(" [OK] UNAVAILABLE JSON report generated")
    
    # Check original file integrity
    new_size = input_ply.stat().st_size
    assert orig_size == new_size, "Original PLY was modified!"
    print(" [OK] Original relative PLY remained completely untouched")
    
    print("--- REAL UAV TEST PASSED (HONESTY VERIFIED) ---\n")

def main():
    parser = argparse.ArgumentParser(description="Test Point Cloud Transformation (Milestone 5)")
    parser.add_argument("--job-id", type=str, required=True, help="Explicit Job ID to read from")
    args = parser.parse_args()

    run_real_test(args.job_id)

if __name__ == "__main__":
    main()
