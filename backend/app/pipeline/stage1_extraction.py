"""
AERO RECON-3D — Stage 1: Frame Extraction & Quality Filtering

Extracts every Nth frame from the input video, measures sharpness via
Laplacian variance, filters out blurry/dark frames, and saves accepted
keyframes as PNG files.

Inputs:  { "video_path": str }
Outputs: { "frame_dir": Path, "frame_paths": list[Path],
           "frame_count": int, "summary": dict }
"""
import cv2
import json
import numpy as np
from pathlib import Path

from .base import PipelineStage
from ..core.config import FRAME_SAMPLE_RATE, MAX_FRAMES, BLUR_THRESHOLD


def _laplacian_variance(gray: np.ndarray) -> float:
    """Return the variance of the Laplacian — higher = sharper."""
    return float(cv2.Laplacian(gray, cv2.CV_64F).var())


class FrameExtractionStage(PipelineStage):

    @property
    def stage_name(self) -> str:
        return "stage1_extraction"

    def run(self, inputs: dict) -> dict:
        self.logger.start()
        video_path = Path(inputs["video_path"])

        if not video_path.exists():
            self.logger.error(f"Video file not found: {video_path}")
            raise FileNotFoundError(str(video_path))

        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            self.logger.error("Cannot open video with OpenCV.")
            raise RuntimeError("Cannot open video.")

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        duration_s = total_frames / fps if fps > 0 else 0

        self.logger.info(
            f"Video: {width}×{height}, {fps:.1f} fps, "
            f"{total_frames} frames, {duration_s:.1f}s"
        )
        self.logger.record(
            video_file=video_path.name,
            resolution=f"{width}x{height}",
            fps=round(fps, 2),
            total_frames=total_frames,
            duration_seconds=round(duration_s, 1),
        )

        frame_dir = self.stage_dir / "frames"
        frame_dir.mkdir(parents=True, exist_ok=True)

        accepted: list[Path] = []
        quality_log: list[dict] = []

        frame_idx = 0
        saved = 0
        blurry_rejected = 0
        dark_rejected = 0

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            if frame_idx % FRAME_SAMPLE_RATE == 0:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                blur_score = _laplacian_variance(gray)
                mean_brightness = float(gray.mean())

                # Reject dark frames (mean < 30 means near-black)
                if mean_brightness < 30:
                    dark_rejected += 1
                    quality_log.append({
                        "frame_idx": frame_idx,
                        "blur_score": round(blur_score, 2),
                        "brightness": round(mean_brightness, 2),
                        "accepted": False,
                        "reject_reason": "dark",
                    })
                    frame_idx += 1
                    continue

                if blur_score < BLUR_THRESHOLD:
                    blurry_rejected += 1
                    quality_log.append({
                        "frame_idx": frame_idx,
                        "blur_score": round(blur_score, 2),
                        "brightness": round(mean_brightness, 2),
                        "accepted": False,
                        "reject_reason": "blurry",
                    })
                    frame_idx += 1
                    continue

                out_path = frame_dir / f"frame_{saved:05d}.png"
                cv2.imwrite(str(out_path), frame)
                accepted.append(out_path)
                quality_log.append({
                    "frame_idx": frame_idx,
                    "blur_score": round(blur_score, 2),
                    "brightness": round(mean_brightness, 2),
                    "accepted": True,
                    "reject_reason": None,
                })
                saved += 1

                if saved >= MAX_FRAMES:
                    self.logger.info(f"MAX_FRAMES ({MAX_FRAMES}) reached — stopping early.")
                    break

            frame_idx += 1

        cap.release()

        # Save quality log
        with open(self.stage_dir / "quality_log.json", "w") as f:
            json.dump(quality_log, f, indent=2)

        self.logger.record(
            frames_sampled=frame_idx,
            frames_accepted=len(accepted),
            frames_blurry_rejected=blurry_rejected,
            frames_dark_rejected=dark_rejected,
            acceptance_rate=f"{100*len(accepted)/max(1,frame_idx//FRAME_SAMPLE_RATE):.1f}%",
        )

        if len(accepted) < 10:
            self.logger.error(
                f"Only {len(accepted)} frames accepted — insufficient for reconstruction."
            )
            summary = self.logger.finish(success=False)
            return {"frame_dir": frame_dir, "frame_paths": accepted,
                    "frame_count": len(accepted), "summary": summary}

        summary = self.logger.finish(success=True)
        return {
            "frame_dir": frame_dir,
            "frame_paths": accepted,
            "frame_count": len(accepted),
            "video_width": width,
            "video_height": height,
            "video_fps": fps,
            "summary": summary,
        }
