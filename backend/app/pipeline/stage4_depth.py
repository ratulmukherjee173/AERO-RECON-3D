"""
AERO RECON-3D — Stage 4: Monocular Depth Estimation

Estimates dense depth maps for each accepted keyframe using MiDaS
(DPT_BEiT_S_256 — small, CPU-friendly model).

Depth maps are relative/inverse-depth in MiDaS output space. They are
saved as 16-bit PNG files for inspection and as numpy arrays for the
next stage.

Inputs:  { "frame_paths": list[Path], "camera_poses": list[dict], ... }
Outputs: { "depth_maps": list[Path], "depth_arrays": list[np.ndarray],
           "summary": dict }
"""
import cv2
import numpy as np
from pathlib import Path

from .base import PipelineStage
from ..core.config import MIDAS_MODEL


class DepthEstimationStage(PipelineStage):

    @property
    def stage_name(self) -> str:
        return "stage4_depth"

    def run(self, inputs: dict) -> dict:
        self.logger.start()

        frame_paths: list[Path] = inputs["frame_paths"]
        camera_poses: list[dict] = inputs["camera_poses"]

        # Only run depth on accepted frames (those with accepted pose)
        accepted_indices = [p["frame_idx"] for p in camera_poses if p["accepted"]]
        accepted_indices = [i for i in accepted_indices if i < len(frame_paths)]

        # ── Load MiDaS ────────────────────────────────────────────────────
        try:
            import torch
            import torchvision.transforms as T
            import contextlib
            import sys
            import io

            self.logger.info(f"Loading MiDaS model: {MIDAS_MODEL}")
            
            # Prevent Errno 22 on Windows detached consoles by redirecting stderr
            dummy_stderr = sys.stdout if sys.stdout is not None else io.StringIO()
            with contextlib.redirect_stderr(dummy_stderr):
                model = torch.hub.load(
                    "intel-isl/MiDaS",
                    MIDAS_MODEL,
                    pretrained=True,
                    trust_repo=True,
                )
                device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
                model = model.to(device).eval()
                self.logger.info(f"MiDaS running on: {device}")

                midas_transforms = torch.hub.load(
                    "intel-isl/MiDaS", "transforms", trust_repo=True
                )
                
            if "small" in MIDAS_MODEL.lower():
                transform = midas_transforms.small_transform
            else:
                transform = midas_transforms.dpt_transform

        except Exception as e:
            self.logger.error(f"MiDaS failed to load ({e}). No fallback permitted.")
            raise RuntimeError(f"Neural depth failed: {e}")

        depth_dir = self.stage_dir / "depth_maps"
        depth_dir.mkdir(parents=True, exist_ok=True)

        depth_map_paths: list[Path] = []
        depth_arrays: list[np.ndarray] = []
        processed = 0

        # Limit depth estimation to avoid very long CPU runs on PoC
        MAX_DEPTH_FRAMES = 60
        indices_to_process = accepted_indices[:MAX_DEPTH_FRAMES]

        self.logger.info(
            f"Running depth on {len(indices_to_process)} of {len(accepted_indices)} accepted frames."
        )

        for fi in indices_to_process:
            fp = frame_paths[fi]
            img_bgr = cv2.imread(str(fp))
            if img_bgr is None:
                continue

            import torch
            img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
            input_batch = transform(img_rgb).to(device)
            with torch.no_grad():
                prediction = model(input_batch)
                prediction = torch.nn.functional.interpolate(
                    prediction.unsqueeze(1),
                    size=img_bgr.shape[:2],
                    mode="bicubic",
                    align_corners=False,
                ).squeeze()
            depth_raw = prediction.cpu().numpy()

            # Normalise to [0, 1]
            d_min, d_max = depth_raw.min(), depth_raw.max()
            if d_max > d_min:
                depth_norm = (depth_raw - d_min) / (d_max - d_min)
            else:
                depth_norm = np.zeros_like(depth_raw)

            depth_arrays.append(depth_norm.astype(np.float32))

            # Save 16-bit PNG
            depth_16 = (depth_norm * 65535).astype(np.uint16)
            out_path = depth_dir / f"depth_{fi:05d}.png"
            cv2.imwrite(str(out_path), depth_16)
            depth_map_paths.append(out_path)
            processed += 1

        self.logger.record(
            depth_model=MIDAS_MODEL,
            frames_depth_estimated=processed,
            depth_map_resolution=f"{depth_arrays[0].shape[1]}x{depth_arrays[0].shape[0]}" if depth_arrays else "N/A",
        )

        if not depth_arrays:
            self.logger.error("No depth maps produced.")
            return {"depth_maps": [], "depth_arrays": [], "accepted_indices": indices_to_process,
                    "summary": self.logger.finish(success=False)}

        summary = self.logger.finish(success=True)
        return {
            "depth_maps": depth_map_paths,
            "depth_arrays": depth_arrays,
            "accepted_indices": indices_to_process,
            "summary": summary,
        }
