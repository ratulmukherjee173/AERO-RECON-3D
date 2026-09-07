import json
import numpy as np
from pathlib import Path
from typing import List, Dict, Any

from .models import CameraTrajectory, CameraTrajectoryPoint

def extract_trajectory(
    poses_json_path: str | Path,
    video_file: str,
    fps: float = 30.0
) -> CameraTrajectory:
    """
    Parses camera_poses.json (from Stage 3) and extracts a CameraTrajectory.
    Does NOT modify or recalculate the pose algorithm.
    """
    poses_path = Path(poses_json_path)
    if not poses_path.exists():
        raise FileNotFoundError(f"Poses file not found: {poses_path}")

    with open(poses_path, "r") as f:
        raw_poses: List[Dict[str, Any]] = json.load(f)

    if not raw_poses:
        raise ValueError("Poses JSON is empty.")

    points = []
    accepted_count = 0
    
    # Ensure monotonically increasing frame indices for sanity
    last_frame_idx = -1

    for pose_data in raw_poses:
        frame_idx = pose_data.get("frame_idx", 0)
        
        if frame_idx <= last_frame_idx:
            # Monotonicity check (Stage 3 processes pairs sequentially, so this should hold)
            raise ValueError(f"Frame indices are not strictly increasing: {last_frame_idx} -> {frame_idx}")
        last_frame_idx = frame_idx
        
        valid = pose_data.get("accepted", False)
        if valid:
            accepted_count += 1
            
        t_list = pose_data.get("t", [0.0, 0.0, 0.0])
        R_list = pose_data.get("R", [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]])
        
        # Flatten t if it's nested, though stage3 flattens it.
        if isinstance(t_list[0], list):
            t_list = [t_list[0][0], t_list[1][0], t_list[2][0]]

        # Compute true camera center: C = -R^T t
        R_np = np.array(R_list, dtype=np.float64)
        t_np = np.array(t_list, dtype=np.float64).reshape(3, 1)
        C_np = -R_np.T @ t_np
        position = C_np.flatten().tolist()

        pt = CameraTrajectoryPoint(
            frame_index=frame_idx,
            timestamp_seconds=float(frame_idx / fps),
            position=position,
            orientation=R_list,
            valid=valid
        )
        points.append(pt)

    return CameraTrajectory(
        video_file=Path(video_file).name,
        fps=fps,
        frame_count=last_frame_idx + 1 if last_frame_idx >= 0 else 0,
        accepted_poses=accepted_count,
        points=points
    )
