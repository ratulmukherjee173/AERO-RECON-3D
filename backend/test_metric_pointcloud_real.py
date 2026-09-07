import argparse
import sys
import json
import hashlib
from pathlib import Path

from app.core.config import OUTPUTS_DIR, DATA_DIR
from app.trajectory.models import AlignmentReport
from app.trajectory.pointcloud_transform import transform_point_cloud

def _hash_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

def run_real_test(job_id: str):
    print("\n--- REAL UAV METRIC POINT CLOUD TEST (HONEST STATUS CHECK) ---")
    
    job_dir = OUTPUTS_DIR / job_id
    stage5_dir = job_dir / "stage5"
    input_ply = stage5_dir / "point_cloud.ply"
    
    if not input_ply.exists():
        print(f"[!] Error: {input_ply} does not exist. Ensure Stage 5 completed.")
        sys.exit(1)
        
    alignment_json = OUTPUTS_DIR / "trajectory" / "drone_flight_01_metric_alignment.json"
    if not alignment_json.exists():
        print(f"[!] Error: {alignment_json} does not exist. Run M12 alignment real test first.")
        sys.exit(1)
        
    with open(alignment_json, "r") as f:
        alignment_data = json.load(f)
        
    alignment_report = AlignmentReport(**alignment_data)
    
    output_ply = OUTPUTS_DIR / "trajectory" / f"{job_id}_metric_point_cloud.ply"
    report_output = OUTPUTS_DIR / "trajectory" / f"{job_id}_metric_point_cloud.json"
    
    # Check integrity before
    original_hash = _hash_file(input_ply)
    
    print("Attempting to generate metric point cloud...")
    report = transform_point_cloud(
        input_ply=input_ply,
        output_ply=output_ply,
        alignment_report=alignment_report,
        report_output=report_output,
        job_id=job_id
    )
    
    # -------------------------------------------
    # VERIFY HONEST UNAVAILABLE DATA HANDLING
    # -------------------------------------------
    assert report["status"] == "METRIC_POINTCLOUD_UNAVAILABLE", "Status must be UNAVAILABLE"
    print(" [OK] Status correctly reports METRIC_POINTCLOUD_UNAVAILABLE")
    
    assert report["scale"] is None, "Scale must be safely None"
    assert report["rotation"] is None, "Rotation must be safely None"
    assert report["translation"] is None, "Translation must be safely None"
    print(" [OK] Metric scale/alignment not hallucinated")
    
    assert not output_ply.exists(), "Metric PLY should not have been generated"
    print(" [OK] No fake metric PLY generated")
    
    # Verify original integrity
    assert original_hash == _hash_file(input_ply), "Original PLY was illegally modified!"
    print(" [OK] Original relative PLY remained completely untouched")
    
    print("--- REAL UAV TEST PASSED (HONESTY VERIFIED) ---\n")

def main():
    parser = argparse.ArgumentParser(description="Test Metric Point Cloud (Milestone 13)")
    parser.add_argument("--job-id", type=str, required=True, help="Explicit Job ID")
    args = parser.parse_args()

    run_real_test(args.job_id)

if __name__ == "__main__":
    main()
