"""
AERO RECON-3D — Pipeline Runner / Orchestrator

Chains all 5 stages and persists a full pipeline report as JSON.

Usage:
    python -m app.pipeline.runner --video path/to/video.mp4 --job my_job
"""
import sys
import json
import time
import uuid
import argparse
import subprocess
from pathlib import Path

from ..core.config import OUTPUTS_DIR
from .stage1_extraction import FrameExtractionStage
from .stage2_features import FeatureTrackingStage
from .stage3_pose import PoseEstimationStage
from .stage4_depth import DepthEstimationStage
from .stage5_pointcloud import PointCloudStage


def run_pipeline(video_path: str | Path, job_id: str | None = None, on_progress=None) -> dict:
    """
    Execute the full 5-stage reconstruction pipeline.

    Parameters
    ----------
    video_path : str | Path
        Path to the input drone video file.
    job_id : str, optional
        Unique job identifier. Auto-generated if not supplied.

    Returns
    -------
    dict
        Full pipeline report with per-stage summaries and final outputs.
    """
    if job_id is None:
        job_id = uuid.uuid4().hex[:8]

    video_path = Path(video_path).resolve()
    job_dir = OUTPUTS_DIR / job_id
    job_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*60}")
    print(f"  AERO RECON-3D - Reconstruction Pipeline")
    print(f"  Job ID : {job_id}")
    print(f"  Video  : {video_path.name}")
    print(f"  Output : {job_dir}")
    print(f"{'='*60}\n")

    pipeline_start = time.perf_counter()
    stage_reports: list[dict] = []
    pipeline_data: dict = {"video_path": str(video_path)}

    stages = [
        ("Stage 1 — Frame Extraction",  FrameExtractionStage,  job_dir / "stage1"),
        ("Stage 2 — Feature Tracking",  FeatureTrackingStage,  job_dir / "stage2"),
        ("Stage 3 — Pose Estimation",   PoseEstimationStage,   job_dir / "stage3"),
        ("Stage 4 — Depth Estimation",  DepthEstimationStage,  job_dir / "stage4"),
        ("Stage 5 — Point Cloud",       PointCloudStage,       job_dir / "stage5"),
    ]

    for i, (label, StageClass, stage_dir) in enumerate(stages):
        print(f"\n{'-'*50}")
        print(f"  {label}")
        print(f"{'-'*50}")
        
        if on_progress:
            # Report stage progress (e.g. 0, 20, 40, 60, 80)
            on_progress(label.split(" — ")[-1], int((i / len(stages)) * 100))

        try:
            stage = StageClass(job_id, stage_dir)
            result = stage.run(pipeline_data)
            pipeline_data.update(result)
            stage_reports.append(result.get("summary", {}))

            if result.get("summary", {}).get("status") == "FAILED":
                print(f"\n[!] {label} reported FAILURE. Pipeline aborting.")
                break

        except Exception as exc:
            import traceback
            print(f"\n[X] {label} raised exception: {exc}")
            try:
                print(traceback.format_exc())
            except OSError:
                pass
            stage_reports.append({"stage": label, "status": "EXCEPTION", "error": str(exc)})
            break
            
    # ── Stage 6 and 7 (Subprocess for Open3D isolation) ───────────────────
    if pipeline_data.get("ply_path") and stage_reports[-1].get("status") != "FAILED" and stage_reports[-1].get("status") != "EXCEPTION":
        current_dir = Path(__file__).resolve().parent
        for i, (label, script_name) in enumerate([
            ("Stage 6 — Mesh Generation", "stage6_mesh.py"),
            ("Stage 7 — Vertex-Colored GLB", "stage7_texture.py")
        ], start=len(stages)):
            print(f"\n{'-'*50}")
            print(f"  {label}")
            print(f"{'-'*50}")
            
            if on_progress:
                on_progress(label.split(" — ")[-1], int((i / (len(stages) + 2)) * 100))
                
            try:
                import sys
                script_path = str(current_dir / script_name)
                res = subprocess.run(
                    [sys.executable, script_path, "--job-id", job_id],
                    capture_output=True, text=True, check=True
                )
                print(res.stdout)
                stage_reports.append({"stage": label, "status": "SUCCESS"})
            except subprocess.CalledProcessError as exc:
                print(f"\n[!] {label} reported FAILURE.")
                print(exc.stdout)
                print(exc.stderr)
                stage_reports.append({"stage": label, "status": "FAILED", "error": exc.stderr})
                break
            except Exception as exc:
                print(f"\n[X] {label} raised exception: {exc}")
                stage_reports.append({"stage": label, "status": "EXCEPTION", "error": str(exc)})
                break

    pipeline_elapsed = time.perf_counter() - pipeline_start
    
    if on_progress:
        on_progress("Finalizing", 95)

    # ── Final report ──────────────────────────────────────────────────────
    ply_path = pipeline_data.get("ply_path")
    point_count = pipeline_data.get("point_count", 0)
    success = ply_path is not None and Path(str(ply_path)).exists()

    report = {
        "job_id": job_id,
        "video_file": str(video_path),
        "status": "SUCCESS" if success else "FAILED",
        "total_elapsed_seconds": round(pipeline_elapsed, 2),
        "ply_path": str(ply_path) if ply_path else None,
        "point_count": point_count,
        "stages": stage_reports,
    }

    report_path = job_dir / "pipeline_report.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)

    print(f"\n{'='*60}")
    print(f"  Pipeline {'SUCCESS [OK]' if success else 'FAILED [ERR]'}")
    print(f"  Elapsed : {pipeline_elapsed:.1f}s")
    if success:
        print(f"  PLY     : {ply_path}")
        print(f"  Points  : {point_count:,}")
    print(f"  Report  : {report_path}")
    print(f"{'='*60}\n")

    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AeroRecon 3D — Reconstruction Pipeline")
    parser.add_argument("--video", required=True, help="Path to drone video file")
    parser.add_argument("--job", default=None, help="Job ID (auto-generated if omitted)")
    args = parser.parse_args()
    result = run_pipeline(args.video, args.job)
    sys.exit(0 if result["status"] == "SUCCESS" else 1)
