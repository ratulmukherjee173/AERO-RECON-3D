import os
import json
import time
import numpy as np
from pathlib import Path

def run_stage6(job_id: str, 
               voxel_size: float = 0.05, 
               poisson_depth: int = 8, 
               density_threshold_percentile: float = 5.0):
    try:
        import open3d as o3d
    except ImportError:
        return {"status": "FAILED", "error": "Open3D not available in this environment."}
    
    print(f"--- STAGE 6: MESH GENERATION (Job: {job_id}) ---")
    start_time = time.time()
    
    # Paths
    base_dir = Path("backend/data/outputs")
    stage5_dir = base_dir / job_id / "stage5"
    stage6_dir = base_dir / job_id / "stage6"
    traj_path = base_dir / "trajectory" / f"{job_id}_trajectory.json"
    
    ply_path = stage5_dir / "point_cloud.ply"
    out_mesh_path = stage6_dir / "mesh.ply"
    out_report_path = stage6_dir / "mesh_report.json"
    
    if not ply_path.exists():
        return {"status": "FAILED", "error": f"Stage 5 point cloud not found at {ply_path}"}
        
    os.makedirs(stage6_dir, exist_ok=True)
    
    report = {
        "job_id": job_id,
        "source_point_cloud": str(ply_path),
        "coordinate_system": "RELATIVE / LOCAL COORDINATES",
        "coordinate_status": "UNAVAILABLE - NO GPS/IMU DATA",
        "voxel_size": voxel_size,
        "poisson_depth": poisson_depth,
        "status": "PROCESSING",
        "warnings": []
    }
    
    try:
        # 1. Load Point Cloud
        print(f"Loading point cloud from {ply_path}...")
        t0 = time.time()
        pcd = o3d.io.read_point_cloud(str(ply_path))
        t1 = time.time()
        report["input_points"] = len(pcd.points)
        report["processing_times"] = {"load_time": t1 - t0}
        print(f"Loaded {len(pcd.points)} points.")
        
        # 2. Voxel Downsampling
        print(f"Voxel downsampling (size={voxel_size})...")
        t0 = time.time()
        downpcd = pcd.voxel_down_sample(voxel_size=voxel_size)
        t1 = time.time()
        report["downsampled_points"] = len(downpcd.points)
        report["processing_times"]["downsample_time"] = t1 - t0
        print(f"Downsampled to {len(downpcd.points)} points.")
        
        # 3. Normal Estimation
        print("Estimating normals...")
        t0 = time.time()
        downpcd.estimate_normals(search_param=o3d.geometry.KDTreeSearchParamHybrid(radius=voxel_size * 4, max_nn=30))
        t1 = time.time()
        report["normal_estimation_parameters"] = {"method": "Hybrid", "radius": voxel_size * 4, "max_nn": 30}
        report["processing_times"]["normal_estimation_time"] = t1 - t0
        
        # 4. Normal Orientation using Camera Centers
        print("Orienting normals towards camera centers...")
        t0 = time.time()
        camera_centers = []
        if traj_path.exists():
            with open(traj_path, "r") as f:
                traj_data = json.load(f)
            for pt in traj_data.get("points", []):
                if pt.get("valid"):
                    R = np.array(pt["orientation"])
                    t = np.array(pt["position"])
                    # C = -R.T @ t
                    C = -np.dot(R.T, t)
                    camera_centers.append(C)
        
        if camera_centers:
            # Orient normals toward cameras
            # Open3D's orient_normals_towards_camera_location takes a single camera location
            # To use multiple cameras, we could compute the average camera center, 
            # or simply point normals towards the origin if cameras orbit the object, 
            # or rely on consistent tangent planes.
            # A common heuristic for UAV flights is orienting towards the average camera center or simply up (if Z is up).
            # For simplicity, we will orient towards the mean camera center.
            mean_camera_center = np.mean(camera_centers, axis=0)
            downpcd.orient_normals_towards_camera_location(mean_camera_center)
            report["normal_orientation_method"] = "oriented_towards_mean_camera_center"
        else:
            # Default orientation if trajectory missing
            downpcd.orient_normals_to_align_with_direction(np.array([0., 0., 1.]))
            report["normal_orientation_method"] = "oriented_towards_z_up"
            report["warnings"].append("Trajectory not found; oriented normals to align with Z-axis")
            
        t1 = time.time()
        report["processing_times"]["normal_orientation_time"] = t1 - t0
        
        # 5. Poisson Reconstruction
        print(f"Poisson surface reconstruction (depth={poisson_depth})...")
        t0 = time.time()
        mesh, densities = o3d.geometry.TriangleMesh.create_from_point_cloud_poisson(
            downpcd, depth=poisson_depth, width=0, scale=1.1, linear_fit=False)
        t1 = time.time()
        report["processing_times"]["poisson_time"] = t1 - t0
        report["mesh_vertices_before_filtering"] = len(mesh.vertices)
        report["mesh_triangles_before_filtering"] = len(mesh.triangles)
        print(f"Generated {len(mesh.vertices)} vertices and {len(mesh.triangles)} triangles.")
        
        # 6. Density Filtering
        print("Filtering low density vertices...")
        t0 = time.time()
        densities = np.asarray(densities)
        if len(densities) > 0:
            density_threshold = np.percentile(densities, density_threshold_percentile)
            vertices_to_remove = densities < density_threshold
            mesh.remove_vertices_by_mask(vertices_to_remove)
            
            report["filtering_method"] = "Poisson_density_percentile"
            report["filtering_threshold_percentile"] = density_threshold_percentile
            report["filtering_threshold_value"] = float(density_threshold)
        t1 = time.time()
        report["processing_times"]["filtering_time"] = t1 - t0
        
        report["mesh_vertices"] = len(mesh.vertices)
        report["mesh_triangles"] = len(mesh.triangles)
        print(f"After filtering: {len(mesh.vertices)} vertices and {len(mesh.triangles)} triangles.")
        
        # 7. Vertex Coloring
        # Poisson creates new vertices, so we need to transfer colors from downpcd to mesh using nearest neighbor.
        print("Transferring colors...")
        t0 = time.time()
        if len(downpcd.colors) > 0:
            pcd_tree = o3d.geometry.KDTreeFlann(downpcd)
            mesh_vertices = np.asarray(mesh.vertices)
            mesh_colors = np.zeros_like(mesh_vertices)
            downpcd_colors = np.asarray(downpcd.colors)
            
            for i in range(len(mesh_vertices)):
                [k, idx, _] = pcd_tree.search_knn_vector_3d(mesh_vertices[i], 1)
                if k > 0:
                    mesh_colors[i] = downpcd_colors[idx[0]]
            
            mesh.vertex_colors = o3d.utility.Vector3dVector(mesh_colors)
            report["color_transfer_method"] = "Nearest_Neighbor"
        else:
            report["color_transfer_method"] = "None (No colors in point cloud)"
        t1 = time.time()
        report["processing_times"]["color_transfer_time"] = t1 - t0
        
        # 8. Export Mesh
        print("Exporting mesh...")
        t0 = time.time()
        o3d.io.write_triangle_mesh(str(out_mesh_path), mesh)
        t1 = time.time()
        report["processing_times"]["export_time"] = t1 - t0
        
        report["status"] = "SUCCESS"
        report["overall_time"] = time.time() - start_time
        
        with open(out_report_path, "w") as f:
            json.dump(report, f, indent=4)
            
        print(f"Mesh generation completed in {report['overall_time']:.2f}s.")
        return report

    except Exception as e:
        report["status"] = "FAILED"
        report["error"] = str(e)
        with open(out_report_path, "w") as f:
            json.dump(report, f, indent=4)
        print(f"Mesh generation failed: {e}")
        return report

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--job-id", required=True)
    parser.add_argument("--voxel-size", type=float, default=0.05)
    parser.add_argument("--poisson-depth", type=int, default=8)
    args = parser.parse_args()
    
    run_stage6(args.job_id, voxel_size=args.voxel_size, poisson_depth=args.poisson_depth)
