from pydantic import BaseModel, Field
from typing import List, Optional, Dict


class CameraIntrinsics(BaseModel):
    width: int
    height: int
    fx: float
    fy: float
    cx: float
    cy: float
    distortion: str = "UNAVAILABLE"
    source: str = "UNAVAILABLE"
    status: str = "UNAVAILABLE"
    estimation_method: str = "UNAVAILABLE"
    assumptions: List[str] = []

class ReprojectionObservation(BaseModel):
    point_3d: List[float] = Field(..., description="[X, Y, Z] world coordinates")
    observed_2d: List[float] = Field(..., description="[u, v] image coordinates")


# ── Validation Thresholds ─────────────────────────────────────────────────
class ValidationThresholds(BaseModel):
    """
    Centralized validation thresholds for triangulation quality assessment.
    Every threshold has a technical justification documented here.
    """

    min_parallax_degrees: float = Field(
        default=1.0,
        description=(
            "Minimum parallax angle (degrees) between the two viewing rays. "
            "Below ~1 degree, the triangulation baseline is nearly degenerate "
            "and triangulated depth becomes extremely sensitive to pixel noise. "
            "Standard photogrammetric practice requires >1-2 degrees."
        ),
    )

    min_baseline_ratio: float = Field(
        default=1e-6,
        description=(
            "Minimum ratio of camera baseline to mean triangulated depth. "
            "When the baseline is negligible relative to depth, triangulation "
            "is numerically unstable (baseline/depth ratio << 1). "
            "1e-6 catches only true degeneracies without filtering normal cases."
        ),
    )

    max_reprojection_error_px: float = Field(
        default=50.0,
        description=(
            "Maximum reprojection error (pixels) for a validated observation. "
            "Errors above this indicate triangulation failure, gross feature "
            "mismatch, or numerical breakdown rather than normal reconstruction "
            "noise. 50 px is deliberately generous to avoid discarding moderate "
            "errors that may reflect real reconstruction quality."
        ),
    )

    max_depth_ratio: float = Field(
        default=1000.0,
        description=(
            "Maximum ratio of triangulated depth to camera baseline. "
            "Very distant points relative to baseline produce unreliable depth. "
            "1000x is a generous upper bound."
        ),
    )


# ── Rejection Reasons ─────────────────────────────────────────────────────
class RejectionBreakdown(BaseModel):
    """
    Machine-readable breakdown of why observations were rejected.
    Each field counts observations rejected for that specific reason.
    An observation may be counted in multiple categories if applicable,
    but is only counted once in the total.
    """

    nonfinite_point: int = 0
    behind_camera: int = 0
    low_parallax: int = 0
    excessive_depth: int = 0
    excessive_reprojection_error: int = 0
    nonfinite_reprojection: int = 0


# ── Statistics Block ──────────────────────────────────────────────────────
class ReprojectionStats(BaseModel):
    """Reusable statistics block for reprojection error distributions."""

    observation_count: int = 0
    rmse: Optional[float] = None
    mae: Optional[float] = None
    median: Optional[float] = None
    min_error: Optional[float] = None
    max_error: Optional[float] = None
    percentile_95: Optional[float] = None
    percentile_99: Optional[float] = None


# ── Reprojection Report (Milestone 7 compatible + Milestone 8 extensions) ─
class ReprojectionReport(BaseModel):
    status: str = "REPROJECTION_UNAVAILABLE"
    units: str = "pixels"
    camera_intrinsics_source: str = "UNAVAILABLE"
    camera_intrinsics: Optional[CameraIntrinsics] = None
    correspondence_method: str = "UNAVAILABLE"
    valid_observations: int = 0
    rejected_observations: int = 0
    rmse: Optional[float] = None
    mae: Optional[float] = None
    median: Optional[float] = None
    min_error: Optional[float] = None
    max_error: Optional[float] = None
    percentile_95: Optional[float] = None
    percentile_99: Optional[float] = None

    # Milestone 8 extensions
    raw_stats: Optional[ReprojectionStats] = None
    validated_stats: Optional[ReprojectionStats] = None
    rejection_breakdown: Optional[RejectionBreakdown] = None
    thresholds: Optional[ValidationThresholds] = None


# ── Unchanged Milestone 6 models ──────────────────────────────────────────
class ReferenceMeasurement(BaseModel):
    measurement_id: str
    description: str
    point_a: List[float] = Field(..., description="[X, Y, Z] reference coordinates")
    point_b: List[float] = Field(..., description="[X, Y, Z] reference coordinates")
    known_distance: float
    units: str
    source: str
    timestamp: Optional[float] = None


class MeasurementResult(BaseModel):
    measurement_id: str
    reconstructed_distance: float
    absolute_error: float
    relative_error: float
    percentage_error: float


class MeasurementValidationReport(BaseModel):
    status: str = "GROUND_TRUTH_UNAVAILABLE"
    units: str = "meters"
    ground_truth_available: bool = False
    valid_measurements: int = 0
    rejected_measurements: int = 0
    rmse: Optional[float] = None
    mae: Optional[float] = None
    median_error: Optional[float] = None
    max_error: Optional[float] = None
    min_error: Optional[float] = None
    mean_percentage_error: Optional[float] = None
    max_percentage_error: Optional[float] = None
    results: List[MeasurementResult] = []


class GeospatialAccuracyReport(BaseModel):
    status: str = "UNAVAILABLE"


class AccuracyReport(BaseModel):
    status: str = "ACCURACY_AVAILABLE"
    reprojection: ReprojectionReport = Field(default_factory=ReprojectionReport)
    metric_measurement: MeasurementValidationReport = Field(
        default_factory=MeasurementValidationReport
    )
    geospatial_accuracy: GeospatialAccuracyReport = Field(
        default_factory=GeospatialAccuracyReport
    )
