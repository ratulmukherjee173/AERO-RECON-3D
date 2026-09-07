from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class GPSRecord(BaseModel):
    timestamp: float
    latitude: float
    longitude: float
    altitude: float
    relative_altitude: Optional[float] = None

class IMURecord(BaseModel):
    timestamp: float
    accel_x: float
    accel_y: float
    accel_z: float
    gyro_x: float
    gyro_y: float
    gyro_z: float

class VideoInfo(BaseModel):
    width: int
    height: int
    fps: float
    frame_count: int
    duration_sec: float

class CameraInfo(BaseModel):
    make: Optional[str] = None
    model: Optional[str] = None
    focal_length_mm: Optional[float] = None
    fov_degrees: Optional[float] = None

class TelemetrySample(BaseModel):
    timestamp: float
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    altitude: Optional[float] = None
    roll: Optional[float] = None
    pitch: Optional[float] = None
    yaw: Optional[float] = None
    velocity_x: Optional[float] = None
    velocity_y: Optional[float] = None
    velocity_z: Optional[float] = None
    accel_x: Optional[float] = None
    accel_y: Optional[float] = None
    accel_z: Optional[float] = None
    gyro_x: Optional[float] = None
    gyro_y: Optional[float] = None
    gyro_z: Optional[float] = None
    source: str

class GPSReferenceTrajectory(BaseModel):
    samples: List[TelemetrySample] = []
    coordinate_system: str = "ENU"
    source: str = "UNAVAILABLE"
    status: str = "GPS_ENU_UNAVAILABLE"

class TelemetrySyncReport(BaseModel):
    video_start_time: Optional[float] = None
    telemetry_start_time: Optional[float] = None
    time_offset: Optional[float] = None
    matched_samples: int = 0
    unmatched_video_frames: int = 0
    unmatched_telemetry_samples: int = 0
    mean_time_difference: Optional[float] = None
    max_time_difference: Optional[float] = None
    synchronization_method: Optional[str] = None
    status: str = "TELEMETRY_SYNC_UNAVAILABLE"

class TelemetryReport(BaseModel):
    source_file: str
    video_info: VideoInfo
    camera_info: Optional[CameraInfo] = None
    gps_records: List[GPSRecord] = []
    imu_records: List[IMURecord] = []
    telemetry_samples: List[TelemetrySample] = []
    has_gps: bool = False
    has_imu: bool = False
    warnings: List[str] = []
    raw_metadata: Dict[str, Any] = {}
    sync_report: Optional[TelemetrySyncReport] = None
