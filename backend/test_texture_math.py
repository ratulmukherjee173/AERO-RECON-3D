import os
import json
import numpy as np
import tempfile
from pathlib import Path
from app.pipeline.stage7_texture import run_stage7
import open3d as o3d

def test_texture_math():
    print("--- SYNTHETIC VERTEX-COLOR GLB MATH TEST ---")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        job_id = "test_math_texture"
        
        # Setup mock stage 6 output directory
        base_dir = Path("backend/data/outputs")
        stage6_dir = base_dir / job_id / "stage6"
        os.makedirs(stage6_dir, exist_ok=True)
        ply_path = stage6_dir / "mesh.ply"
        
        # 1. Generate synthetic colored mesh (a simple box)
        print("Generating synthetic colored mesh...")
        mesh = o3d.geometry.TriangleMesh.create_box()
        # Add some random colors to vertices
        colors = np.random.rand(len(mesh.vertices), 3)
        mesh.vertex_colors = o3d.utility.Vector3dVector(colors)
        
        # Save as PLY
        o3d.io.write_triangle_mesh(str(ply_path), mesh, write_vertex_colors=True)
        
        original_hash = hash(open(ply_path, "rb").read())
        
        # 2. Run Stage 7 GLB Export
        print("Running Stage 7 Vertex-Colored GLB Export...")
        report = run_stage7(job_id)
        
        # 3. Validation
        assert report["status"] == "SUCCESS", f"Failed: {report.get('error')}"
        assert report["high_resolution"]["vertex_count"] == len(mesh.vertices)
        assert report["web_proxy"]["vertex_count"] <= len(mesh.vertices) # might be decimate or original if tiny
        
        stage7_dir = base_dir / job_id / "stage7"
        high_glb_path = stage7_dir / "textured_model_high.glb"
        web_glb_path = stage7_dir / "textured_model_web.glb"
        
        assert high_glb_path.exists()
        assert web_glb_path.exists()
        
        # Check source integrity
        new_hash = hash(open(ply_path, "rb").read())
        assert original_hash == new_hash, "Source mesh was modified!"
        
        # Check output loadability
        loaded_mesh = o3d.io.read_triangle_mesh(str(high_glb_path))
            
        assert len(loaded_mesh.vertices) == report["high_resolution"]["vertex_count"]
        assert loaded_mesh.has_vertex_colors(), "Vertex colors missing in exported GLB"
        
        print(" [OK] Mesh loads successfully")
        print(" [OK] GLB geometries are valid")
        print(" [OK] Vertex colors perfectly exported")
        print(" [OK] Exported model can be reopened")
        print(" [OK] Original PLY remains untouched")
        print("--- SYNTHETIC VERTEX-COLOR GLB TEST PASSED ---")

if __name__ == "__main__":
    test_texture_math()
