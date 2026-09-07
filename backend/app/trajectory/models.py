from pydantic import BaseModel, Field
from typing import List, Literal, Optional

class CameraTrajectoryPoint(BaseModel):
    frame_index: int
    timestamp_seconds: float
    position: List[float] = Field(..., description="[x, y, z] relative translation")
    orientation: List[List[float]] = Field(..., description="3x3 rotation matrix")
    valid: bool

class RigidTransform(BaseModel):
    translation: List[float] = Field(..., description="[x, y, z]")
    rotation: List[List[float]] = Field(..., description="3x3 rotation matrix")
    scale: float

class CameraTrajectory(BaseModel):
    video_file: str
    fps: float
    frame_count: int
    accepted_poses: int
    trajectory_type: Literal["RELATIVE_CAMERA_TRAJECTORY"] = "RELATIVE_CAMERA_TRAJECTORY"
    timestamp_source: str = "VIDEO_FRAME_INDEX"
    coordinate_convention: str = "OpenCV (X right, Y down, Z forward)"
    points: List[CameraTrajectoryPoint]
    
    # Required Status Flags
    scale_status: str = "UNAVAILABLE"
    sync_status: str = "NO_TELEMETRY"
    metric: bool = False
    georeferenced: bool = False
    
    # Milestone 11 separate boolean statuses
    gps_available: bool = False
    gps_enu_available: bool = False
    telemetry_sync_available: bool = False
    camera_gps_correspondence_available: bool = False
    metric_alignment_available: bool = False
    imu_available: bool = False
    
    warnings: List[str] = []

class MetricReferencePoint(BaseModel):
    timestamp: float
    position: List[float] = Field(..., description="[x, y, z] metric coordinates")
    valid: bool

class MetricReferenceTrajectory(BaseModel):
    source: str
    coordinate_system: str = Field(..., description="e.g. ENU, WGS84")
    units: str = Field(..., description="e.g. meters, degrees")
    points: List[MetricReferencePoint]

class AlignmentErrorStats(BaseModel):
    rmse: float
    mae: float
    median: float
    p95: float
    p99: float
    max: float

class AlignmentReport(BaseModel):
    source_video: str
    camera_trajectory_source: str = "STAGE3_POSE"
    reference_source: str = "UNAVAILABLE"
    sync_status: str = "UNAVAILABLE"
    matched_point_count: int = 0
    scale_status: str = "METRIC_SCALE_UNAVAILABLE"
    alignment_status: str = "METRIC_ALIGNMENT_UNAVAILABLE"
    
    transform_direction: Optional[str] = None
    scale: Optional[float] = None
    scale_units: Optional[str] = None
    rotation: Optional[List[List[float]]] = None
    translation: Optional[List[float]] = None
    
    timestamp_statistics: Optional[dict] = None
    before_alignment_errors: Optional[AlignmentErrorStats] = None
    after_alignment_errors: Optional[AlignmentErrorStats] = None
    error_units: str = "meters"
    
    coordinate_system: str = "RELATIVE"
    units: str = "RELATIVE_UNITS"
    enu_origin: Optional[List[float]] = None
    metric: bool = False
    georeferenced: bool = False
    warnings: List[str] = []
