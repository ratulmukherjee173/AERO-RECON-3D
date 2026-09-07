"""
AERO RECON-3D — Stage-by-Stage Test Script

Runs Stage 1 alone against the test video to verify frame extraction works
before running the full pipeline.

Usage:
    python backend/test_stage1.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.app.core.config import SAMPLES_DIR, OUTPUTS_DIR
from backend.app.pipeline.stage1_extraction import FrameExtractionStage

VIDEO = SAMPLES_DIR / "test_drone.mp4"
JOB_ID = "test_s1"
STAGE_DIR = OUTPUTS_DIR / JOB_ID / "stage1"

if not VIDEO.exists():
    print(f"[X] Test video not found: {VIDEO}")
    print("   Run: python backend/generate_test_video.py first.")
    sys.exit(1)

print(f"Testing Stage 1 with: {VIDEO}")
stage = FrameExtractionStage(JOB_ID, STAGE_DIR)
result = stage.run({"video_path": str(VIDEO)})

print(f"\n✔  Stage 1 complete")
print(f"   Accepted frames: {result['frame_count']}")
print(f"   Frame dir: {result['frame_dir']}")
print(f"   Status: {result['summary']['status']}")
