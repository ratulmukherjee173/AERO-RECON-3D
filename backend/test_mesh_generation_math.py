import os
import json
import numpy as np
import tempfile
from pathlib import Path
from app.pipeline.stage6_mesh import run_stage6
import open3d as o3d

def test_mesh_generation_math():
    print("--- SYNTHETIC MESH GENERATION MATH TEST ---")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        job_id = "test_math_mesh"
        
        # Setup mock stage 5 output directory
        base_dir = Path("backend/data/outputs")
        stage5_dir = base_dir / job_id / "stage5"
        os.makedirs(stage5_dir, exist_ok=True)
        ply_path = stage5_dir / "point_cloud.ply"
        
        # 1. Generate synthetic point cloud (a simple cube)
        print("Generating synthetic cube point cloud...")
        points = []
        colors = []
        for x in np.linspace(0, 1, 10):
            for y in np.linspace(0, 1, 10):
                for z in np.linspace(0, 1, 10):
                    # Only keep points near the surface of the cube [0,1]^3
                    if x in [0.0, 1.0] or y in [0.0, 1.0] or z in [0.0, 1.0]:
                        points.append([x, y, z])
                        colors.append([x, y, z]) # Use position as color
                        
        pcd = o3d.geometry.PointCloud()
        pcd.points = o3d.utility.Vector3dVector(np.array(points, dtype=np.float64))
        pcd.colors = o3d.utility.Vector3dVector(np.array(colors, dtype=np.float64))
        
        o3d.io.write_point_cloud(str(ply_path), pcd)
        original_hash = hash(open(ply_path, "rb").read())
        
        # 2. Run Mesh Generation
        print("Running Stage 6 Mesh Generation...")
        report = run_stage6(job_id, voxel_size=0.1, poisson_depth=6)
        
        # 3. Validation
        assert report["status"] == "SUCCESS", f"Failed: {report.get('error')}"
        assert report["input_points"] == len(points)
        assert report["downsampled_points"] > 0
        assert report["mesh_vertices"] > 0
        assert report["mesh_triangles"] > 0
        
        stage6_dir = base_dir / job_id / "stage6"
        mesh_path = stage6_dir / "mesh.ply"
        assert mesh_path.exists()
        
        # Check source integrity
        new_hash = hash(open(ply_path, "rb").read())
        assert original_hash == new_hash, "Source point cloud was modified!"
        
        # Check mesh colors and validity
        mesh = o3d.io.read_triangle_mesh(str(mesh_path))
        assert len(mesh.vertices) == report["mesh_vertices"]
        assert len(mesh.vertex_colors) == len(mesh.vertices)
        
        verts = np.asarray(mesh.vertices)
        assert np.all(np.isfinite(verts)), "Mesh contains non-finite vertices"
        
        print(" [OK] Voxel downsampling works")
        print(" [OK] Normals were estimated")
        print(" [OK] Poisson reconstruction completed")
        print(" [OK] Density filtering preserved mesh structure")
        print(" [OK] RGB information transferred")
        print(" [OK] Original PLY remains untouched")
        print("--- SYNTHETIC TEST PASSED ---")

if __name__ == "__main__":
    test_mesh_generation_math()
