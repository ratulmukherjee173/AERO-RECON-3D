"""
AERO RECON-3D — Stage 5: Point Cloud Generation

Backprojects each depth map into 3D using the estimated camera pose and
intrinsics, accumulates points across all frames, then cleans the cloud
via Statistical Outlier Removal and optional voxel downsampling.

Exports the final point cloud as a .PLY file (ASCII + per-vertex colour).

Inputs:  { "depth_arrays", "accepted_indices", "camera_poses",
           "frame_paths", "K", "intrinsics", ... }
Outputs: { "ply_path": Path, "point_count": int, "summary": dict }
"""
import cv2
import json
import numpy as np
import math
from pathlib import Path

from .base import PipelineStage
from ..core.config import VOXEL_SIZE, SOR_NB_NEIGHBORS, SOR_STD_RATIO, MAX_DEPTH


def _backproject_depth(
    depth: np.ndarray,
    K: np.ndarray,
    R: np.ndarray,
    t: np.ndarray,
    color: np.ndarray,
    max_depth: float = 50.0,
    stride: int = 4,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Backproject a depth map into world-space 3D points.

    Parameters
    ----------
    depth  : H×W float32 normalised depth [0,1]
    K      : 3×3 intrinsic matrix
    R      : 3×3 rotation (world←camera)
    t      : 3-vector translation (world position)
    color  : H×W×3 uint8 BGR image
    stride : pixel subsampling stride

    Returns
    -------
    points : N×3 world-space xyz
    colors : N×3 float rgb [0,1]
    """
    H, W = depth.shape
    fx, fy = K[0, 0], K[1, 1]
    cx, cy = K[0, 2], K[1, 2]

    ys = np.arange(0, H, stride)
    xs = np.arange(0, W, stride)
    xv, yv = np.meshgrid(xs, ys)

    d = depth[yv, xv]

    # Scale normalised depth to a metric-like range
    # (up to max_depth — absolute scale unknown without GPS)
    z = d * max_depth
    mask = (z > 0.1) & (z < max_depth)

    x_cam = (xv[mask] - cx) * z[mask] / fx
    y_cam = (yv[mask] - cy) * z[mask] / fy
    z_cam = z[mask]

    pts_cam = np.stack([x_cam, y_cam, z_cam], axis=1)  # N×3

    # Transform to world frame: p_world = R^T @ (p_cam - t)
    R_inv = R.T
    pts_world = (R_inv @ (pts_cam - t.reshape(1, 3)).T).T

    # Colour lookup
    col = color[yv[mask], xv[mask]].astype(np.float32) / 255.0  # BGR
    col_rgb = col[:, ::-1]  # → RGB

    return pts_world.astype(np.float32), col_rgb.astype(np.float32)


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
        
        # Create a structured array for fast binary writing
        dt = np.dtype([
            ('x', 'f4'), ('y', 'f4'), ('z', 'f4'),
            ('red', 'u1'), ('green', 'u1'), ('blue', 'u1')
        ])
        
        data = np.empty(n, dtype=dt)
        data['x'] = points[:, 0].astype(np.float32)
        data['y'] = points[:, 1].astype(np.float32)
        data['z'] = points[:, 2].astype(np.float32)
        
        colors_u8 = (colors * 255).clip(0, 255).astype(np.uint8)
        data['red'] = colors_u8[:, 0]
        data['green'] = colors_u8[:, 1]
        data['blue'] = colors_u8[:, 2]
        
        f.write(data.tobytes())


class PointCloudStage(PipelineStage):

    @property
    def stage_name(self) -> str:
        return "stage5_pointcloud"

    def run(self, inputs: dict) -> dict:
        self.logger.start()

        depth_arrays: list[np.ndarray] = inputs["depth_arrays"]
        accepted_indices: list[int] = inputs["accepted_indices"]
        camera_poses: list[dict] = inputs["camera_poses"]
        frame_paths: list[Path] = inputs["frame_paths"]
        K: np.ndarray = inputs["K"]

        # Build pose lookup by frame index
        pose_by_frame = {p["frame_idx"]: p for p in camera_poses}

        all_points: list[np.ndarray] = []
        all_colors: list[np.ndarray] = []

        self.logger.info(
            f"Backprojecting {len(depth_arrays)} depth maps into 3D…"
        )

        for idx, (fi, depth) in enumerate(zip(accepted_indices, depth_arrays)):
            pose = pose_by_frame.get(fi)
            if pose is None or not pose.get("accepted", True):
                continue

            R = np.array(pose["R"], dtype=np.float64)
            t = np.array(pose["t"], dtype=np.float64)

            # Load colour image
            color_bgr = cv2.imread(str(frame_paths[fi]))
            if color_bgr is None:
                continue

            # Resize colour to match depth resolution
            h, w = depth.shape
            color_resized = cv2.resize(color_bgr, (w, h))

            pts, cols = _backproject_depth(
                depth, K, R, t, color_resized,
                max_depth=MAX_DEPTH,
                stride=3,   # every 3rd pixel → good density/speed balance
            )
            if len(pts) > 0:
                all_points.append(pts)
                all_colors.append(cols)

        if not all_points:
            self.logger.error("No points generated from any depth map.")
            return {"ply_path": None, "point_count": 0,
                    "summary": self.logger.finish(success=False)}

        merged_pts = np.concatenate(all_points, axis=0)
        merged_cols = np.concatenate(all_colors, axis=0)
        raw_count = len(merged_pts)
        self.logger.info(f"Raw point count before filtering: {raw_count:,}")

        # ── Statistical Outlier Removal (SOR) ─────────────────────────────
        try:
            import open3d as o3d
            pcd = o3d.geometry.PointCloud()
            pcd.points = o3d.utility.Vector3dVector(merged_pts.astype(np.float64))
            pcd.colors = o3d.utility.Vector3dVector(merged_cols.astype(np.float64))

            pcd, inlier_idx = pcd.remove_statistical_outlier(
                nb_neighbors=SOR_NB_NEIGHBORS,
                std_ratio=SOR_STD_RATIO,
            )
            self.logger.info(f"After SOR: {len(pcd.points):,} points.")

            if VOXEL_SIZE > 0:
                pcd = pcd.voxel_down_sample(voxel_size=VOXEL_SIZE)
                self.logger.info(f"After voxel downsample: {len(pcd.points):,} points.")

            merged_pts = np.asarray(pcd.points, dtype=np.float32)
            merged_cols = np.asarray(pcd.colors, dtype=np.float32)
            use_open3d = True

        except ImportError:
            self.logger.warning("Open3D not available — skipping SOR. Writing raw cloud.")
            use_open3d = False

        # ── Export PLY ────────────────────────────────────────────────────
        ply_path = self.stage_dir / "point_cloud.ply"
        _save_ply(ply_path, merged_pts, merged_cols)

        # ── Generate Preview PLY ──────────────────────────────────────────
        preview_ply_path = self.stage_dir / "preview.ply"
        # Deterministic downsample for browser visualization
        target_preview_points = 200_000
        step = max(1, math.ceil(len(merged_pts) / target_preview_points))
        preview_pts = merged_pts[::step]
        preview_cols = merged_cols[::step]
        _save_ply(preview_ply_path, preview_pts, preview_cols)

        final_count = len(merged_pts)
        self.logger.record(
            raw_point_count=raw_count,
            final_point_count=final_count,
            outliers_removed=raw_count - final_count,
            ply_file=str(ply_path),
            preview_ply_file=str(preview_ply_path),
            preview_point_count=len(preview_pts),
            open3d_used=use_open3d,
        )

        summary = self.logger.finish(success=True)
        return {
            "ply_path": ply_path,
            "preview_ply_path": preview_ply_path,
            "point_count": final_count,
            "preview_point_count": len(preview_pts),
            "summary": summary,
        }
