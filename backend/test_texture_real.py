import argparse
import json
from pathlib import Path
from app.pipeline.stage7_texture import run_stage7

def test_texture_real(job_id: str):
    print(f"--- REAL UAV VERTEX-COLOR GLB TEST (Job: {job_id}) ---")
    
    base_dir = Path("backend/data/outputs")
    stage6_dir = base_dir / job_id / "stage6"
    mesh_path = stage6_dir / "mesh.ply"
    
    if not mesh_path.exists():
        print(f"FAILED: Stage 6 Mesh not found at {mesh_path}")
        return
        
    original_hash = hash(open(mesh_path, "rb").read())
    
    print("Running pipeline...")
    report = run_stage7(job_id)
    
    if report["status"] != "SUCCESS":
        print(f"GLB export failed: {report.get('error')}")
        return
        
    print("\n--- RESULTS ---")
    print(f"High-Res Vertices: {report.get('high_resolution', {}).get('vertex_count')}")
    print(f"High-Res Triangles: {report.get('high_resolution', {}).get('triangle_count')}")
    print(f"Web Proxy Vertices: {report.get('web_proxy', {}).get('vertex_count')}")
    print(f"Web Proxy Triangles: {report.get('web_proxy', {}).get('triangle_count')}")
    
    out_sizes = report.get('output_file_sizes', {})
    print(f"High-Res GLB Size: {out_sizes.get('textured_model_high.glb', 0) / 1024 / 1024:.2f} MB")
    print(f"Web Proxy GLB Size: {out_sizes.get('textured_model_web.glb', 0) / 1024 / 1024:.2f} MB")
    
    print(f"Processing Time: {report.get('overall_time'):.2f}s")
    print(f"Coordinate System: {report.get('coordinate_system')}")
    
    new_hash = hash(open(mesh_path, "rb").read())
    assert original_hash == new_hash, "Original Mesh was modified!"
    print(" [OK] Original Mesh remains untouched")
    
    # Check output loadability
    stage7_dir = base_dir / job_id / "stage7"
    assert (stage7_dir / "textured_model_high.glb").exists(), "High-Res GLB not found!"
    assert (stage7_dir / "textured_model_web.glb").exists(), "Web Proxy GLB not found!"
    assert report["validation"]["high_res_colors_present"], "High-res colors missing!"
    
    print(" [OK] Output GLBs exist and validated")
    print("--- REAL UAV TEST PASSED ---")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--job-id", required=True)
    args = parser.parse_args()
    test_texture_real(args.job_id)
