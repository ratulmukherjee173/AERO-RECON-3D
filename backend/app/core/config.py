"""
AERO RECON-3D — Backend Configuration
"""
import os
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent.parent  # backend/
DATA_DIR = BASE_DIR / "data"
SAMPLES_DIR = DATA_DIR / "samples"
OUTPUTS_DIR = DATA_DIR / "outputs"
UPLOADS_DIR = DATA_DIR / "uploads"

for d in [SAMPLES_DIR, OUTPUTS_DIR, UPLOADS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ── Stage 1: Frame Extraction ──────────────────────────────────────────────
FRAME_SAMPLE_RATE: int = 5          # extract every Nth frame from video
MAX_FRAMES: int = 300               # hard cap to keep PoC fast
BLUR_THRESHOLD: float = 10.0        # Laplacian variance below this = blurry (10 is lenient, suits drone footage)

# ── Stage 2: Feature Detection ──────────────────────────────────────────────
MAX_KEYPOINTS: int = 2000           # SIFT max features per frame
LOWE_RATIO: float = 0.75            # Lowe's ratio test threshold
MIN_MATCHES: int = 30               # minimum good matches to proceed

# ── Stage 3: Pose Estimation ──────────────────────────────────────────────
RANSAC_PROB: float = 0.999          # RANSAC confidence
RANSAC_THRESHOLD: float = 1.0       # RANSAC inlier pixel threshold (px)
MIN_INLIERS: int = 20               # min inlier count to accept pose

# ── Stage 4: Depth Estimation ──────────────────────────────────────────────
# MiDaS model name — MiDaS_small is small & runs on CPU
MIDAS_MODEL: str = "MiDaS_small"

# ── Stage 5: Point Cloud ──────────────────────────────────────────────────
VOXEL_SIZE: float = 0.05            # Open3D voxel grid downsampling
SOR_NB_NEIGHBORS: int = 20          # Statistical outlier removal neighbours
SOR_STD_RATIO: float = 2.0          # SOR standard deviation ratio
MAX_DEPTH: float = 50.0             # clip depth beyond this (metres, scale-relative)
