import cv2
import json
from pathlib import Path
import csv
from typing import List
from .models import TelemetryReport, VideoInfo, CameraInfo, TelemetrySample

class TelemetryExtractor:
    def __init__(self, video_path: str):
        self.video_path = Path(video_path)
    
    def _parse_srt(self, srt_path: Path) -> List[TelemetrySample]:
        import re
        samples = []
        with open(srt_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Split by empty lines to get subtitle blocks
        blocks = re.split(r'\n\s*\n', content.strip())
        
        # Regexes for various DJI formats
        # Bracketed format: [latitude: 37.123] [rel_alt: 10.5]
        re_lat = re.compile(r'latitude:\s*([-.\d]+)', re.IGNORECASE)
        re_lon = re.compile(r'longitude:\s*([-.\d]+)', re.IGNORECASE)
        re_rel_alt = re.compile(r'rel_alt:\s*([-.\d]+)', re.IGNORECASE)
        re_abs_alt = re.compile(r'abs_alt:\s*([-.\d]+)', re.IGNORECASE)
        
        # GPS format: GPS(-122.1234, 37.1234, 12) or GPS(lon, lat, alt)
        re_gps = re.compile(r'GPS\s*\(\s*([-.\d]+)\s*,\s*([-.\d]+)\s*(?:,\s*([-.\d]+))?\s*\)', re.IGNORECASE)
        
        # Attitude/OSD
        re_yaw = re.compile(r'osd_yaw:\s*([-.\d]+)', re.IGNORECASE)
        re_pitch = re.compile(r'osd_pitch:\s*([-.\d]+)', re.IGNORECASE)
        re_roll = re.compile(r'osd_roll:\s*([-.\d]+)', re.IGNORECASE)
        
        # Timestamp (00:00:01,000 --> ...)
        re_time = re.compile(r'(\d{2}):(\d{2}):(\d{2}),(\d{3})\s*-->')
        
        for block in blocks:
            lines = block.split('\n')
            if len(lines) < 3:
                continue
                
            time_match = re_time.search(lines[1])
            if not time_match:
                continue
                
            h, m, s, ms = map(int, time_match.groups())
            timestamp = h * 3600 + m * 60 + s + ms / 1000.0
            
            data_text = " ".join(lines[2:])
            
            lat, lon, alt = None, None, None
            
            # Try bracket format first
            lat_m = re_lat.search(data_text)
            lon_m = re_lon.search(data_text)
            abs_m = re_abs_alt.search(data_text)
            rel_m = re_rel_alt.search(data_text)
            
            if lat_m and lon_m:
                lat = float(lat_m.group(1))
                lon = float(lon_m.group(1))
            
            if abs_m:
                alt = float(abs_m.group(1))
            elif rel_m:
                alt = float(rel_m.group(1))
                
            # Fallback to GPS() format
            if lat is None and lon is None:
                gps_m = re_gps.search(data_text)
                if gps_m:
                    lon = float(gps_m.group(1))
                    lat = float(gps_m.group(2))
                    if gps_m.group(3) and alt is None:
                        alt = float(gps_m.group(3))
                        
            yaw, pitch, roll = None, None, None
            yaw_m = re_yaw.search(data_text)
            pitch_m = re_pitch.search(data_text)
            roll_m = re_roll.search(data_text)
            if yaw_m: yaw = float(yaw_m.group(1))
            if pitch_m: pitch = float(pitch_m.group(1))
            if roll_m: roll = float(roll_m.group(1))
            
            samples.append(TelemetrySample(
                timestamp=timestamp,
                latitude=lat,
                longitude=lon,
                altitude=alt,
                yaw=yaw,
                pitch=pitch,
                roll=roll,
                source=srt_path.name
            ))
            
        return samples

    def _read_external_telemetry(self) -> List[TelemetrySample]:
        upload_dir = self.video_path.parent
        base_name = self.video_path.stem
        
        json_path = upload_dir / f"{base_name}_telemetry.json"
        csv_path = upload_dir / f"{base_name}_telemetry.csv"
        srt_path = upload_dir / f"{base_name}_telemetry.srt"
        
        # Fallback to older telemetry dir if needed
        legacy_telemetry_dir = self.video_path.parent.parent / "telemetry"
        if not srt_path.exists() and not json_path.exists() and not csv_path.exists():
            json_path = legacy_telemetry_dir / f"{base_name}_telemetry.json"
            csv_path = legacy_telemetry_dir / f"{base_name}_telemetry.csv"
            srt_path = legacy_telemetry_dir / f"{base_name}_telemetry.srt"
            
        samples = []
        
        if srt_path.exists():
            return self._parse_srt(srt_path)
        elif json_path.exists():
            source_name = json_path.name
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for item in data:
                    samples.append(TelemetrySample(**item, source=source_name))
        elif csv_path.exists():
            source_name = csv_path.name
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    sample_dict = {"source": source_name}
                    for k, v in row.items():
                        if v and v.strip() != "":
                            try:
                                sample_dict[k] = float(v)
                            except ValueError:
                                pass
                    if 'timestamp' in sample_dict:
                        samples.append(TelemetrySample(**sample_dict))
                        
        return samples

    def extract(self) -> TelemetryReport:
        if not self.video_path.exists():
            raise FileNotFoundError(f"Video not found: {self.video_path}")
        
        cap = cv2.VideoCapture(str(self.video_path))
        if not cap.isOpened():
            raise ValueError(f"Could not open video: {self.video_path}")
        
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = float(cap.get(cv2.CAP_PROP_FPS))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        duration = frame_count / fps if fps > 0 else 0
        cap.release()
        
        video_info = VideoInfo(
            width=width,
            height=height,
            fps=fps,
            frame_count=frame_count,
            duration_sec=duration
        )
        
        telemetry_samples = self._read_external_telemetry()
        
        has_gps = False
        has_imu = False
        
        if telemetry_samples:
            has_gps = any(s.latitude is not None and s.longitude is not None for s in telemetry_samples)
            has_imu = any(s.accel_x is not None or s.gyro_x is not None for s in telemetry_samples)
            warnings = []
        else:
            warnings = ["GPS/IMU metadata not available in this video."]
        
        report = TelemetryReport(
            source_file=self.video_path.name,
            video_info=video_info,
            camera_info=None,
            gps_records=[],
            imu_records=[],
            telemetry_samples=telemetry_samples,
            has_gps=has_gps,
            has_imu=has_imu,
            warnings=warnings
        )
        return report

    def extract_and_save(self, output_path: str):
        report = self.extract()
        out_file = Path(output_path)
        out_file.parent.mkdir(parents=True, exist_ok=True)
        with open(out_file, 'w', encoding='utf-8') as f:
            f.write(report.model_dump_json(indent=2))
        return report

if __name__ == "__main__":
    # Ensure correct relative path when run directly
    base_dir = Path(__file__).resolve().parent.parent.parent
    video_path = base_dir / "data" / "samples" / "drone_flight_01.mp4"
    out_path = base_dir / "data" / "outputs" / "telemetry" / "drone_flight_01_metadata.json"
    
    extractor = TelemetryExtractor(str(video_path))
    extractor.extract_and_save(str(out_path))
    print(f"Extraction complete. Saved to {out_path}")
