"""
AERO RECON-3D — Stage 3: Camera Pose Estimation

Estimates the relative camera pose (R, t) for each accepted frame pair using
the 5-point Essential Matrix algorithm with RANSAC.

Assumes pinhole camera model with focal length estimated from image diagonal
(Hartley/Zisserman heuristic when no EXIF/GPS metadata is available).

Produces an ordered list of camera positions and orientations in a consistent
coordinate frame via incremental chaining.

Inputs : { "kps_serialisable", "descs_list", "good_matches_list",
            "video_width", "video_height", ... }
Outputs: { "camera_poses": list[dict],  # [{"R": ndarray, "t": ndarray}]
           "intrinsics": dict,           # {"fx","fy","cx","cy"}
           "summary": dict }
"""
import cv2
import json
import pickle
import numpy as np
from pathlib import Path

from .base import PipelineStage
from ..core.config import RANSAC_PROB, RANSAC_THRESHOLD, MIN_INLIERS


def _build_intrinsics(width: int, height: int, video_path: str = None) -> tuple[np.ndarray, dict]:
    """
    Attempt to extract camera intrinsics from metadata. If unavailable,
    estimate camera intrinsics assuming FOV ≈ 70° (typical drone camera).
    Focal length in pixels ≈ 0.85 × max(W, H).
    """
    # OpenCV cannot extract EXIF/lens metadata from MP4, and ffprobe/exiftool 
    # are not available. We explicitly fall back to estimation.
    source = "ESTIMATED"
    
    f = 0.85 * max(width, height)
    cx = width / 2.0
    cy = height / 2.0
    K = np.array([[f, 0, cx],
                  [0, f, cy],
                  [0, 0, 1.0]], dtype=np.float64)
    
    k_dict = {
        "width": width,
        "height": height,
        "fx": f,
        "fy": f,
        "cx": cx,
        "cy": cy,
        "distortion": "UNAVAILABLE",
        "source": source,
        "status": "ESTIMATED",
        "estimation_method": "focal_length_from_image_diagonal_heuristic",
        "assumptions": [
            "pinhole_camera_model",
            "zero_distortion",
            "focal_length = 0.85 * max(width, height)",
            "principal_point_at_image_center"
        ]
    }
    return K, k_dict


class PoseEstimationStage(PipelineStage):

    @property
    def stage_name(self) -> str:
        return "stage3_pose"

    def run(self, inputs: dict) -> dict:
        self.logger.start()

        kps_serialisable = inputs["kps_serialisable"]
        good_matches_list = inputs["good_matches_list"]
        width = inputs.get("video_width", 1920)
        height = inputs.get("video_height", 1080)
        video_path = inputs.get("video_path")

        K, K_dict = _build_intrinsics(width, height, video_path)
        
        self.logger.info("--- Camera Intrinsics ---")
        self.logger.info(f"Source       : {K_dict['source']}")
        self.logger.info(f"Video Width  : {K_dict['width']}")
        self.logger.info(f"Video Height : {K_dict['height']}")
        self.logger.info(f"fx           : {K_dict['fx']:.2f}")
        self.logger.info(f"fy           : {K_dict['fy']:.2f}")
        self.logger.info(f"cx           : {K_dict['cx']:.2f}")
        self.logger.info(f"cy           : {K_dict['cy']:.2f}")
        self.logger.info("-------------------------")

        self.logger.record(
            intrinsics_source=K_dict["source"],
            fx=round(K_dict["fx"], 2),
            fy=round(K_dict["fy"], 2),
            cx=round(K_dict["cx"], 2),
            cy=round(K_dict["cy"], 2)
        )

        # ── Incremental pose chaining ─────────────────────────────────────
        # Start at identity, then chain relative poses
        poses: list[dict] = [{
            "frame_idx": 0,
            "R": np.eye(3).tolist(),
            "t": np.zeros(3).tolist(),
            "inliers": -1,
            "accepted": True,
        }]

        R_global = np.eye(3, dtype=np.float64)
        t_global = np.zeros((3, 1), dtype=np.float64)
        accepted = 0
        rejected = 0

        for pair_idx, matches in enumerate(good_matches_list):
            if len(matches) < MIN_INLIERS:
                self.logger.warning(
                    f"Pair {pair_idx}-{pair_idx+1}: only {len(matches)} matches, skipping."
                )
                rejected += 1
                poses.append({
                    "frame_idx": pair_idx + 1,
                    "R": R_global.tolist(),
                    "t": t_global.flatten().tolist(),
                    "inliers": 0,
                    "accepted": False,
                })
                continue

            # Unpack match points
            pts1 = np.array([[m[2][0], m[2][1]] for m in matches], dtype=np.float64)
            pts2 = np.array([[m[3][0], m[3][1]] for m in matches], dtype=np.float64)

            E, mask = cv2.findEssentialMat(
                pts1, pts2, K,
                method=cv2.RANSAC,
                prob=RANSAC_PROB,
                threshold=RANSAC_THRESHOLD,
            )
            if E is None:
                self.logger.warning(f"Pair {pair_idx}: Essential matrix failed.")
                rejected += 1
                poses.append({
                    "frame_idx": pair_idx + 1,
                    "R": R_global.tolist(),
                    "t": t_global.flatten().tolist(),
                    "inliers": 0,
                    "accepted": False,
                })
                continue

            inlier_count = int(mask.sum()) if mask is not None else 0

            if inlier_count < MIN_INLIERS:
                self.logger.warning(
                    f"Pair {pair_idx}: only {inlier_count} RANSAC inliers, skipping."
                )
                rejected += 1
                poses.append({
                    "frame_idx": pair_idx + 1,
                    "R": R_global.tolist(),
                    "t": t_global.flatten().tolist(),
                    "inliers": inlier_count,
                    "accepted": False,
                })
                continue

            # Recover pose
            pts1_in = pts1[mask.ravel() == 1]
            pts2_in = pts2[mask.ravel() == 1]
            _, R_rel, t_rel, _ = cv2.recoverPose(E, pts1_in, pts2_in, K)

            # Chain into global frame
            t_global = R_rel @ t_global + t_rel
            R_global = R_rel @ R_global

            accepted += 1
            poses.append({
                "frame_idx": pair_idx + 1,
                "R": R_global.tolist(),
                "t": t_global.flatten().tolist(),
                "inliers": inlier_count,
                "accepted": True,
            })

        # Save poses JSON
        with open(self.stage_dir / "camera_poses.json", "w") as f:
            json.dump(poses, f, indent=2)

        # Save numpy arrays for next stage
        R_arrays = [np.array(p["R"]) for p in poses]
        t_arrays = [np.array(p["t"]).reshape(3, 1) for p in poses]
        with open(self.stage_dir / "poses.pkl", "wb") as f:
            pickle.dump({"R_list": R_arrays, "t_list": t_arrays, "K": K}, f)

        self.logger.record(
            total_pairs=len(good_matches_list),
            poses_accepted=accepted,
            poses_rejected=rejected,
            acceptance_rate=f"{100*accepted/max(1,len(good_matches_list)):.1f}%",
        )

        if accepted < 3:
            self.logger.error("Too few accepted poses for reconstruction.")
            return {"camera_poses": poses, "intrinsics": K_dict, "K": K,
                    "R_list": R_arrays, "t_list": t_arrays,
                    "summary": self.logger.finish(success=False)}

        summary = self.logger.finish(success=True)
        return {
            "camera_poses": poses,
            "intrinsics": K_dict,
            "K": K,
            "R_list": R_arrays,
            "t_list": t_arrays,
            "summary": summary,
        }
