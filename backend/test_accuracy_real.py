"""
AERO RECON-3D — Real UAV Accuracy Test (Milestone 7 + 8)

Connects the accuracy framework to REAL existing pipeline outputs.
Reports BOTH raw and validated reprojection statistics.

Correspondence method:
    Stage 2 matched 2D keypoints (pt_i, pt_j)
    + Stage 3 camera poses (R_i, t_i), (R_j, t_j)
    → Triangulate 3D world point
    → Validate triangulation geometry (parallax, depth, baseline)
    → Reproject 3D point back into both cameras
    → Measure reprojection error in PIXELS

This test does NOT establish metric or geospatial accuracy.
It measures image-space reprojection consistency only.
"""

import argparse
import sys
import json
import math
from pathlib import Path
from datetime import datetime, timezone

from app.core.config import OUTPUTS_DIR, DATA_DIR
from app.accuracy import compute_real_reprojection, AccuracyReport
from app.accuracy.models import (
    ReprojectionReport,
    MeasurementValidationReport,
    GeospatialAccuracyReport,
)


def run_real_test(job_id: str):
    print(f"\n--- REAL UAV ACCURACY TEST (Job: {job_id}) ---")

    job_dir = OUTPUTS_DIR / job_id
    stage2_dir = job_dir / "stage2"
    stage3_dir = job_dir / "stage3"

    if not stage2_dir.exists():
        print(f"[!] Error: {stage2_dir} does not exist.")
        sys.exit(1)
    if not stage3_dir.exists():
        print(f"[!] Error: {stage3_dir} does not exist.")
        sys.exit(1)

    # Verify source artifact sizes before test
    feature_pkl = stage2_dir / "feature_data.pkl"
    poses_pkl = stage3_dir / "poses.pkl"
    ply_path = job_dir / "stage5" / "point_cloud.ply"

    sizes_before = {}
    for p in [feature_pkl, poses_pkl, ply_path]:
        if p.exists():
            sizes_before[str(p)] = p.stat().st_size

    # ── Compute real reprojection with validation ─────────────────────────
    print("Computing real reprojection error from Stage 2 + Stage 3 data...")
    reproj_report = compute_real_reprojection(stage2_dir, stage3_dir)

    # ── Build full accuracy report ────────────────────────────────────────
    accuracy_report = AccuracyReport(
        reprojection=reproj_report,
        metric_measurement=MeasurementValidationReport(
            status="GROUND_TRUTH_UNAVAILABLE",
            ground_truth_available=False,
        ),
        geospatial_accuracy=GeospatialAccuracyReport(status="UNAVAILABLE"),
    )

    # ── Display raw statistics ────────────────────────────────────────────
    if reproj_report.status == "REPROJECTION_AVAILABLE":
        raw = reproj_report.raw_stats
        val = reproj_report.validated_stats
        rej = reproj_report.rejection_breakdown

        print(f"\n [OK] Status: REPROJECTION_AVAILABLE")
        print(f" [OK] Correspondence method: {reproj_report.correspondence_method}")
        print(f" [OK] Camera intrinsics source: {reproj_report.camera_intrinsics_source}")

        print(f"\n --- RAW REPROJECTION ERROR ---")
        print(f" [OK] Observations: {raw.observation_count}")
        print(f" [OK] Min: {raw.min_error:.4f} px")
        print(f" [OK] RMSE: {raw.rmse:.4f} px")
        print(f" [OK] MAE: {raw.mae:.4f} px")
        print(f" [OK] Median: {raw.median:.4f} px")
        print(f" [OK] P95: {raw.percentile_95:.4f} px")
        print(f" [OK] P99: {raw.percentile_99:.4f} px")
        print(f" [OK] Max: {raw.max_error:.4f} px")

        print(f"\n --- VALIDATED REPROJECTION ERROR ---")
        print(f" [OK] Observations: {val.observation_count}")
        if val.observation_count > 0:
            print(f" [OK] Min: {val.min_error:.4f} px")
            print(f" [OK] RMSE: {val.rmse:.4f} px")
            print(f" [OK] MAE: {val.mae:.4f} px")
            print(f" [OK] Median: {val.median:.4f} px")
            print(f" [OK] P95: {val.percentile_95:.4f} px")
            print(f" [OK] P99: {val.percentile_99:.4f} px")
            print(f" [OK] Max: {val.max_error:.4f} px")

        print(f"\n --- REJECTION BREAKDOWN ---")
        print(f"   Nonfinite point: {rej.nonfinite_point}")
        print(f"   Behind camera: {rej.behind_camera}")
        print(f"   Low parallax: {rej.low_parallax}")
        print(f"   Excessive depth: {rej.excessive_depth}")
        print(f"   Excessive reproj error: {rej.excessive_reprojection_error}")
        print(f"   Nonfinite reprojection: {rej.nonfinite_reprojection}")

        print(f"\n --- THRESHOLDS ---")
        th = reproj_report.thresholds
        print(f"   Min parallax: {th.min_parallax_degrees}°")
        print(f"   Min baseline ratio: {th.min_baseline_ratio}")
        print(f"   Max reproj error: {th.max_reprojection_error_px} px")
        print(f"   Max depth ratio: {th.max_depth_ratio}")

        # Sanity checks
        assert raw.observation_count > 0, "Must have raw observations"
        assert raw.rmse >= 0, "RMSE must be non-negative"
        assert math.isfinite(raw.rmse), "RMSE must be finite"
        assert raw.max_error >= raw.mae, "Max must be >= mean"
        assert reproj_report.units == "pixels", "Units must be pixels"
        assert reproj_report.correspondence_method == "TWO_VIEW_TRIANGULATION"

        # Validated RMSE must be <= raw RMSE when validated has observations
        if val.observation_count > 0:
            assert val.rmse <= raw.rmse + 1e-6, "Validated RMSE must be <= raw RMSE"

        print("\n [OK] All sanity checks passed")

    elif reproj_report.status == "REPROJECTION_UNAVAILABLE":
        print(" [OK] Status correctly reports REPROJECTION_UNAVAILABLE")

    # ── Verify metric/geospatial remain UNAVAILABLE ───────────────────────
    assert accuracy_report.metric_measurement.status == "GROUND_TRUTH_UNAVAILABLE"
    print(" [OK] Metric measurement correctly reports GROUND_TRUTH_UNAVAILABLE")

    assert accuracy_report.metric_measurement.ground_truth_available is False
    print(" [OK] Ground truth flag correctly reports False")

    assert accuracy_report.geospatial_accuracy.status == "UNAVAILABLE"
    print(" [OK] Geospatial accuracy correctly reports UNAVAILABLE")

    assert accuracy_report.metric_measurement.rmse is None
    print(" [OK] No fake metric RMSE generated")

    # ── Verify source artifact integrity ──────────────────────────────────
    for p_str, size_before in sizes_before.items():
        p = Path(p_str)
        if p.exists():
            size_after = p.stat().st_size
            assert size_before == size_after, f"Source artifact modified: {p}"
    print(" [OK] All source artifacts remain untouched")

    print("--- REAL UAV TEST PASSED ---\n")

    # ── Write accuracy report ─────────────────────────────────────────────
    out_dir = DATA_DIR / "outputs" / "accuracy"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"{job_id}_accuracy.json"

    with open(out_file, "w") as f:
        json.dump(accuracy_report.model_dump(), f, indent=2)

    print(f"Accuracy JSON written to: {out_file}")

    # ── Write extended validation report ──────────────────────────────────
    val_file = out_dir / "drone_flight_01_validation.json"
    validation_doc = {
        "job_id": job_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "camera_convention": "X_camera = R @ X_world + t",
        "camera_center_convention": "C = -R.T @ t",
        "intrinsics_source": reproj_report.camera_intrinsics_source,
        "correspondence_method": reproj_report.correspondence_method,
        "raw_statistics": reproj_report.raw_stats.model_dump() if reproj_report.raw_stats else None,
        "validated_statistics": reproj_report.validated_stats.model_dump() if reproj_report.validated_stats else None,
        "thresholds": reproj_report.thresholds.model_dump() if reproj_report.thresholds else None,
        "rejection_breakdown": reproj_report.rejection_breakdown.model_dump() if reproj_report.rejection_breakdown else None,
        "limitations": [
            "REPROJECTION_ACCURACY_IS_IMAGE_SPACE_ONLY",
            "METRIC_ACCURACY_UNAVAILABLE",
            "CAMERA_INTRINSICS_ARE_ESTIMATED_NOT_CALIBRATED",
            "GPS_UNAVAILABLE",
            "IMU_UNAVAILABLE",
            "GROUND_TRUTH_UNAVAILABLE",
        ],
        "validation_status": reproj_report.status,
    }
    with open(val_file, "w") as f:
        json.dump(validation_doc, f, indent=2)

    print(f"Validation JSON written to: {val_file}")

    # ── Write intrinsics report ───────────────────────────────────────────
    intrinsics_file = out_dir / "drone_flight_01_intrinsics.json"
    intrinsics_doc = {
        "job_id": job_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    if reproj_report.camera_intrinsics:
        intrinsics_doc.update(reproj_report.camera_intrinsics.model_dump())
    else:
        intrinsics_doc.update({
            "status": "UNAVAILABLE",
            "source": "UNAVAILABLE"
        })

    intrinsics_doc["limitations"] = [
        "METRIC_ACCURACY_UNAVAILABLE",
        "CENTIMETER_ACCURACY_UNAVAILABLE",
        "GEOSPATIAL_ACCURACY_UNAVAILABLE",
        "CALIBRATION_UNAVAILABLE_IF_ESTIMATED"
    ]

    with open(intrinsics_file, "w") as f:
        json.dump(intrinsics_doc, f, indent=2)

    print(f"Intrinsics JSON written to: {intrinsics_file}")


def main():
    parser = argparse.ArgumentParser(description="Test Accuracy Integration (Milestone 7+8)")
    parser.add_argument("--job-id", type=str, required=True, help="Explicit Job ID")
    args = parser.parse_args()

    run_real_test(args.job_id)


if __name__ == "__main__":
    main()
