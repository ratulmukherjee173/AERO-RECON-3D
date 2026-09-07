import sys
import os
import shutil
from pathlib import Path

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).parent))

from app.pipeline.runner import run_pipeline as run_recon_pipeline
from app.core.config import DATA_DIR, OUTPUTS_DIR

def run_pipeline():
    video_path = DATA_DIR / "samples" / "drone_flight_01.mp4"
    if not video_path.exists():
        print(f"Error: {video_path} not found.")
        return

    job_id = "test_m3_correction"
    job_dir = OUTPUTS_DIR / job_id
    
    if job_dir.exists():
        shutil.rmtree(job_dir)
        
    print(f"Starting pipeline for job {job_id}...")
    try:
        results = run_recon_pipeline(str(video_path), job_id)
        if results.get("status") == "SUCCESS":
            print("Pipeline completed successfully!")
        else:
            print("Pipeline failed!")
            sys.exit(1)
    except Exception as e:
        print(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_pipeline()
