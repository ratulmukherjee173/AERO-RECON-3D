import argparse
import json
from pathlib import Path
from app.pipeline.stage6_mesh import run_stage6

def test_mesh_generation_real(job_id: str):
    print(f"--- REAL UAV MESH GENERATION TEST (Job: {job_id}) ---")
    
    base_dir = Path("backend/data/outputs")
    stage5_dir = base_dir / job_id / "stage5"
    ply_path = stage5_dir / "point_cloud.ply"
    
    if not ply_path.exists():
        print(f"FAILED: Stage 5 PLY not found at {ply_path}")
        return
        
    original_hash = hash(open(ply_path, "rb").read())
    
    print("Running pipeline...")
    # Using voxel_size 0.05 and poisson_depth 9 as a conservative baseline for the real UAV
    report = run_stage6(job_id, voxel_size=0.05, poisson_depth=9, density_threshold_percentile=5.0)
    
    if report["status"] != "SUCCESS":
        print(f"Mesh generation failed: {report.get('error')}")
        return
        
    print("\n--- RESULTS ---")
    print(f"Input Points: {report.get('input_points')}")
    print(f"Downsampled Points: {report.get('downsampled_points')}")
    print(f"Mesh Vertices: {report.get('mesh_vertices')}")
    print(f"Mesh Triangles: {report.get('mesh_triangles')}")
    print(f"Processing Time: {report.get('overall_time'):.2f}s")
    print(f"Coordinate System: {report.get('coordinate_system')}")
    
    new_hash = hash(open(ply_path, "rb").read())
    assert original_hash == new_hash, "Original PLY was modified!"
    print(" [OK] Original PLY remains untouched")
    print("--- REAL UAV TEST PASSED ---")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--job-id", required=True)
    args = parser.parse_args()
    test_mesh_generation_real(args.job_id)
