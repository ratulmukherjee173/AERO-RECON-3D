import os
import json
import time
import hashlib
import numpy as np
import open3d as o3d
import trimesh
from pathlib import Path

def calculate_sha256(filepath):
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def export_glb_trimesh(mesh_o3d, out_path):
    # Convert o3d to trimesh
    vertices = np.asarray(mesh_o3d.vertices)
    faces = np.asarray(mesh_o3d.triangles)
    
    mesh_tri = trimesh.Trimesh(vertices=vertices, faces=faces, process=False)
    if mesh_o3d.has_vertex_colors():
        # o3d colors are 0-1 float, trimesh expects 0-255 uint8
        colors = (np.asarray(mesh_o3d.vertex_colors) * 255.0).astype(np.uint8)
        mesh_tri.visual.vertex_colors = colors
        
    scene = trimesh.Scene(mesh_tri)
    scene.export(str(out_path))

def run_stage7(job_id: str):
    print(f"--- STAGE 7: VERTEX-COLORED GLB EXPORT (Job: {job_id}) ---")
    start_time = time.time()
    # Ensure we use the absolute path from config to avoid relative path resolution bugs when deployed
    from backend.app.core.config import OUTPUTS_DIR
    base_dir = OUTPUTS_DIR
    stage6_dir = base_dir / job_id / "stage6"
    stage7_dir = base_dir / job_id / "stage7"
    
    mesh_path = stage6_dir / "mesh.ply"
    if not mesh_path.exists():
        return {"status": "FAILED", "error": f"Stage 6 mesh not found at {mesh_path}"}
        
    os.makedirs(stage7_dir, exist_ok=True)
    out_high_path = stage7_dir / "textured_model_high.glb"
    out_web_path = stage7_dir / "textured_model_web.glb"
    out_safe_path = stage7_dir / "textured_model_safe.glb"
    out_report_path = stage7_dir / "vertex_color_report.json"
    
    report = {
        "job_id": job_id,
        "source_mesh": str(mesh_path),
        "export_type": "VERTEX_COLOR_GLTF/GLB",
        "uv_mapping": "NOT USED",
        "texture_atlas": "NOT USED",
        "color_source": "Stage 6 vertex colors",
        "coordinate_system": "RELATIVE / LOCAL COORDINATES",
        "coordinate_status": "UNAVAILABLE - NO GPS/IMU DATA",
        "master_mesh_preserved": True,
        "status": "PROCESSING",
        "processing_times": {}
    }
    
    try:
        # 1. Source Integrity
        t0 = time.time()
        sha256_before = calculate_sha256(mesh_path)
        report["source_sha256_before"] = sha256_before
        
        # 2. Load Mesh
        print("Loading authoritative Stage 6 mesh...")
        mesh = o3d.io.read_triangle_mesh(str(mesh_path))
        t1 = time.time()
        report["processing_times"]["load_time"] = t1 - t0
        
        if not mesh.has_vertex_colors():
            return {"status": "FAILED", "error": "Mesh has no vertex colors."}
            
        vertices = np.asarray(mesh.vertices)
        faces = np.asarray(mesh.triangles)
        colors = np.asarray(mesh.vertex_colors)
        
        report["high_resolution"] = {
            "vertex_count": len(vertices),
            "triangle_count": len(faces)
        }
        print(f"Authoritative Master: {len(vertices)} vertices, {len(faces)} triangles.")
        
        # 3. High-Resolution GLB Export
        print("Exporting high-resolution GLB...")
        t0 = time.time()
        export_glb_trimesh(mesh, out_high_path)
        t1 = time.time()
        report["processing_times"]["high_res_export"] = t1 - t0
        
        # 4. Web Proxy GLB Export (250k)
        print("Generating 250k Web Proxy...")
        t0 = time.time()
        # Clean mesh to prevent bad geometry
        mesh.remove_degenerate_triangles()
        mesh.remove_duplicated_triangles()
        mesh.remove_duplicated_vertices()
        mesh.remove_non_manifold_edges()
        
        mesh_web = mesh.simplify_quadric_decimation(target_number_of_triangles=250000)
        
        web_vertices = np.asarray(mesh_web.vertices)
        web_faces = np.asarray(mesh_web.triangles)
        
        report["web_proxy"] = {
            "vertex_count": len(web_vertices),
            "triangle_count": len(web_faces),
            "label": "WEB PROXY / DERIVATIVE"
        }
        
        print(f"Web Proxy: {len(web_vertices)} vertices, {len(web_faces)} triangles.")
        print("Exporting web proxy GLB...")
        
        
        export_glb_trimesh(mesh_web, out_web_path)
        t1 = time.time()
        report["processing_times"]["web_proxy_generation"] = t1 - t0
        
        # 4.5 Browser-Safe GLB Export (150k)
        print("Generating 150k Safe Browser Proxy...")
        t0 = time.time()
        mesh_safe = mesh.simplify_quadric_decimation(target_number_of_triangles=150000)
        
        safe_vertices = np.asarray(mesh_safe.vertices)
        safe_faces = np.asarray(mesh_safe.triangles)
        
        report["safe_proxy"] = {
            "vertex_count": len(safe_vertices),
            "triangle_count": len(safe_faces),
            "label": "SAFE BROWSER PROXY"
        }
        
        print(f"Safe Proxy: {len(safe_vertices)} vertices, {len(safe_faces)} triangles.")
        print("Exporting safe proxy GLB...")
        
        export_glb_trimesh(mesh_safe, out_safe_path)
        t1 = time.time()
        report["processing_times"]["safe_proxy_generation"] = t1 - t0
        
        # 5. Validation
        print("Validating outputs...")
        t0 = time.time()
        
        # Load high-res GLB back to verify
        val_mesh_high = trimesh.load(str(out_high_path), process=False)
        # GLB loads as a Scene, extract geometry
        if isinstance(val_mesh_high, trimesh.Scene):
            val_geom_high = list(val_mesh_high.geometry.values())[0]
        else:
            val_geom_high = val_mesh_high
            
        if not hasattr(val_geom_high.visual, 'vertex_colors') or val_geom_high.visual.vertex_colors is None:
            raise ValueError("High-res GLB is missing vertex colors after export!")
            
        val_colors = np.asarray(val_geom_high.visual.vertex_colors)
        if len(val_colors) != report["high_resolution"]["vertex_count"]:
            raise ValueError("High-res GLB vertex count mismatch!")
            
        # Load web proxy GLB back to verify
        val_mesh_web = trimesh.load(str(out_web_path), process=False)
        if isinstance(val_mesh_web, trimesh.Scene):
            val_geom_web = list(val_mesh_web.geometry.values())[0]
        else:
            val_geom_web = val_mesh_web
            
        if not hasattr(val_geom_web.visual, 'vertex_colors') or val_geom_web.visual.vertex_colors is None:
            raise ValueError("Web proxy GLB is missing vertex colors after export!")
            
        # Load safe proxy GLB back to verify
        val_mesh_safe = trimesh.load(str(out_safe_path), process=False)
        if isinstance(val_mesh_safe, trimesh.Scene):
            val_geom_safe = list(val_mesh_safe.geometry.values())[0]
        else:
            val_geom_safe = val_mesh_safe
            
        if not hasattr(val_geom_safe.visual, 'vertex_colors') or val_geom_safe.visual.vertex_colors is None:
            raise ValueError("Safe proxy GLB is missing vertex colors after export!")
            
        extents = val_geom_safe.bounding_box.extents
        
        t1 = time.time()
        report["processing_times"]["validation_time"] = t1 - t0
        
        report["validation"] = {
            "high_res_loads": True,
            "high_res_colors_present": True,
            "web_proxy_loads": True,
            "web_proxy_colors_present": True,
            "safe_proxy_loads": True,
            "safe_proxy_colors_present": True,
            "rgb_min": float(val_colors[:, :3].min()),
            "rgb_max": float(val_colors[:, :3].max()),
            "bounding_box_extents": extents.tolist(),
            "geometry_finite": bool(np.all(np.isfinite(np.asarray(val_geom_safe.vertices))))
        }
        
        # Source Integrity Verification
        sha256_after = calculate_sha256(mesh_path)
        report["source_sha256_after"] = sha256_after
        if sha256_before != sha256_after:
            raise RuntimeError("CRITICAL ERROR: Original Stage 6 mesh was modified during processing!")
            
        report["output_file_sizes"] = {
            "textured_model_high.glb": os.path.getsize(out_high_path),
            "textured_model_web.glb": os.path.getsize(out_web_path),
            "textured_model_safe.glb": os.path.getsize(out_safe_path)
        }
        
        report["status"] = "SUCCESS"
        report["overall_time"] = time.time() - start_time
        
        # Write report
        with open(out_report_path, "w") as f:
            json.dump(report, f, indent=4)
            
        print(f"Vertex-Colored GLB exported in {report['overall_time']:.2f}s.")
        return report

    except Exception as e:
        report["status"] = "FAILED"
        report["error"] = str(e)
        with open(out_report_path, "w") as f:
            json.dump(report, f, indent=4)
        print(f"GLB export failed: {e}")
        return report

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--job-id", required=True)
    args = parser.parse_args()
    
    run_stage7(args.job_id)
