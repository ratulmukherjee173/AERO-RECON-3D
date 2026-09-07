"""
AERO RECON-3D — Stage 2: Feature Detection & Matching

Uses OpenCV SIFT to detect keypoints in each accepted frame.
Performs sequential pairwise matching between adjacent frame pairs
using FLANN + Lowe's ratio test.

Inputs:  { "frame_paths": list[Path], "frame_count": int, ... }
Outputs: { "keypoints_list": list,
           "descriptors_list": list,
           "matches_list": list[list[cv2.DMatch]],
           "match_count": int,
           "summary": dict }
"""
import cv2
import json
import pickle
import numpy as np
from pathlib import Path

from .base import PipelineStage
from ..core.config import MAX_KEYPOINTS, LOWE_RATIO, MIN_MATCHES


class FeatureTrackingStage(PipelineStage):

    @property
    def stage_name(self) -> str:
        return "stage2_features"

    def run(self, inputs: dict) -> dict:
        self.logger.start()
        frame_paths: list[Path] = inputs["frame_paths"]

        if len(frame_paths) < 2:
            self.logger.error("Need at least 2 frames for feature matching.")
            raise ValueError("Insufficient frames.")

        # ── Initialise SIFT detector ───────────────────────────────────────
        sift = cv2.SIFT_create(nfeatures=MAX_KEYPOINTS)
        self.logger.info(f"SIFT initialised with max {MAX_KEYPOINTS} keypoints.")

        # FLANN parameters for SIFT (float descriptors)
        flann_params = dict(algorithm=1, trees=5)   # FLANN_INDEX_KDTREE
        search_params = dict(checks=50)
        flann = cv2.FlannBasedMatcher(flann_params, search_params)

        # ── Detect features in each frame ─────────────────────────────────
        self.logger.info(f"Detecting SIFT features in {len(frame_paths)} frames…")
        kps_serialisable: list[list[dict]] = []
        descs_list: list[np.ndarray | None] = []
        kp_counts: list[int] = []

        for i, fp in enumerate(frame_paths):
            img = cv2.imread(str(fp), cv2.IMREAD_GRAYSCALE)
            if img is None:
                self.logger.warning(f"Could not read {fp.name}, skipping.")
                kps_serialisable.append([])
                descs_list.append(None)
                kp_counts.append(0)
                continue

            kps, desc = sift.detectAndCompute(img, None)
            kp_counts.append(len(kps))

            # Serialise keypoints for JSON log
            kps_serialisable.append([
                {"x": kp.pt[0], "y": kp.pt[1], "size": kp.size, "angle": kp.angle}
                for kp in kps
            ])
            descs_list.append(desc)

        avg_kp = np.mean(kp_counts) if kp_counts else 0
        self.logger.record(
            frames_processed=len(frame_paths),
            avg_keypoints_per_frame=round(avg_kp, 1),
            total_keypoints_detected=int(sum(kp_counts)),
        )

        # ── Sequential pairwise matching ──────────────────────────────────
        self.logger.info("Running sequential FLANN pairwise matching…")
        matches_data: list[dict] = []
        good_matches_list: list[list] = []  # list of (i, j, pt_i, pt_j) tuples
        total_good = 0

        for i in range(len(descs_list) - 1):
            d1 = descs_list[i]
            d2 = descs_list[i + 1]

            if d1 is None or d2 is None or len(d1) < 2 or len(d2) < 2:
                good_matches_list.append([])
                matches_data.append({"pair": (i, i+1), "good_matches": 0, "accepted": False})
                continue

            raw_matches = flann.knnMatch(d1, d2, k=2)

            # Lowe's ratio test
            good = []
            for pair in raw_matches:
                if len(pair) == 2:
                    m, n = pair
                    if m.distance < LOWE_RATIO * n.distance:
                        # Store as (queryIdx, trainIdx, pt_in_frame_i, pt_in_frame_i+1)
                        kp_i = kps_serialisable[i][m.queryIdx]
                        kp_j = kps_serialisable[i+1][m.trainIdx]
                        good.append((m.queryIdx, m.trainIdx,
                                     [kp_i["x"], kp_i["y"]],
                                     [kp_j["x"], kp_j["y"]]))

            accepted = len(good) >= MIN_MATCHES
            total_good += len(good)
            good_matches_list.append(good)
            matches_data.append({
                "pair": [i, i+1],
                "good_matches": len(good),
                "accepted": accepted,
            })

        # Save match metadata
        with open(self.stage_dir / "matches.json", "w") as f:
            json.dump(matches_data, f, indent=2)

        # Save keypoint data (pickle for speed)
        with open(self.stage_dir / "keypoints_serialisable.json", "w") as f:
            # Truncate for file size — only save per-frame counts
            json.dump([{"frame": i, "kp_count": len(k)} for i, k in enumerate(kps_serialisable)], f, indent=2)

        # Pickle full data for next stage
        with open(self.stage_dir / "feature_data.pkl", "wb") as f:
            pickle.dump({
                "kps_serialisable": kps_serialisable,
                "descs_list": descs_list,
                "good_matches_list": good_matches_list,
            }, f)

        accepted_pairs = sum(1 for m in matches_data if m["accepted"])
        self.logger.record(
            total_pairs=len(descs_list) - 1,
            accepted_pairs=accepted_pairs,
            total_good_matches=total_good,
            avg_good_matches_per_pair=round(total_good / max(1, len(descs_list)-1), 1),
        )

        if accepted_pairs < 3:
            self.logger.error("Too few accepted frame pairs — reconstruction will fail.")
            return {"kps_serialisable": kps_serialisable, "descs_list": descs_list,
                    "good_matches_list": good_matches_list, "match_count": total_good,
                    "summary": self.logger.finish(success=False)}

        summary = self.logger.finish(success=True)
        return {
            "kps_serialisable": kps_serialisable,
            "descs_list": descs_list,
            "good_matches_list": good_matches_list,
            "match_count": total_good,
            "accepted_pairs": accepted_pairs,
            "summary": summary,
        }
