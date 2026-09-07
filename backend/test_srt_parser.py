import unittest
from pathlib import Path
import tempfile
import json
import csv
from app.telemetry.extractor import TelemetryExtractor

class TestSRTParser(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base_dir = Path(self.temp_dir.name)
        self.video_path = self.base_dir / "test_video.mp4"
        # Mock video file
        self.video_path.touch()
        
    def tearDown(self):
        self.temp_dir.cleanup()
        
    def test_valid_bracket_srt(self):
        srt_content = """1
00:00:01,000 --> 00:00:02,000
[iso: 100] [shutter: 1/120.0] [fnum: 2.8] [ev: 0] [ct: 5500] [color_md: default] [focal_len: 24.00] [latitude: 37.123] [longitude: -122.123] [rel_alt: 12.3] [abs_alt: 123.4] [osd_yaw: -45.1] [osd_pitch: 1.2] [osd_roll: 0.1]

2
00:00:02,000 --> 00:00:03,000
[latitude: 37.124] [longitude: -122.124] [rel_alt: 15.0]
"""
        srt_path = self.base_dir / "test_video_telemetry.srt"
        srt_path.write_text(srt_content)
        
        extractor = TelemetryExtractor(str(self.video_path))
        samples = extractor._read_external_telemetry()
        
        self.assertEqual(len(samples), 2)
        self.assertEqual(samples[0].latitude, 37.123)
        self.assertEqual(samples[0].longitude, -122.123)
        self.assertEqual(samples[0].altitude, 123.4) # Prefer abs
        self.assertEqual(samples[0].yaw, -45.1)
        self.assertEqual(samples[0].timestamp, 1.0)
        
        self.assertEqual(samples[1].altitude, 15.0) # Fallback to rel
        
    def test_valid_gps_format_srt(self):
        srt_content = """1
00:00:01,000 --> 00:00:02,000
HOME(-122.1234,37.1234) 2023.01.01 12:00:00 GPS(-122.123, 37.123, 100.5) BAROMETER:100.5
"""
        srt_path = self.base_dir / "test_video_telemetry.srt"
        srt_path.write_text(srt_content)
        
        extractor = TelemetryExtractor(str(self.video_path))
        samples = extractor._read_external_telemetry()
        
        self.assertEqual(len(samples), 1)
        self.assertEqual(samples[0].latitude, 37.123)
        self.assertEqual(samples[0].longitude, -122.123)
        self.assertEqual(samples[0].altitude, 100.5)

    def test_missing_fields(self):
        srt_content = """1
00:00:01,000 --> 00:00:02,000
[iso: 100] [shutter: 1/120.0] [rel_alt: 12.3]
"""
        srt_path = self.base_dir / "test_video_telemetry.srt"
        srt_path.write_text(srt_content)
        
        extractor = TelemetryExtractor(str(self.video_path))
        samples = extractor._read_external_telemetry()
        
        self.assertEqual(len(samples), 1)
        self.assertIsNone(samples[0].latitude)
        self.assertEqual(samples[0].altitude, 12.3)

    def test_malformed_record(self):
        srt_content = """1
bad timestamp line -->
[latitude: 37.123] [longitude: -122.123]

2
00:00:02,000 --> 00:00:03,000
[latitude: 37.124] [longitude: -122.124] [rel_alt: 15.0]
"""
        srt_path = self.base_dir / "test_video_telemetry.srt"
        srt_path.write_text(srt_content)
        
        extractor = TelemetryExtractor(str(self.video_path))
        samples = extractor._read_external_telemetry()
        
        # First record should be skipped, second should be parsed
        self.assertEqual(len(samples), 1)
        self.assertEqual(samples[0].timestamp, 2.0)

    def test_csv_compatibility(self):
        csv_path = self.base_dir / "test_video_telemetry.csv"
        with open(csv_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['timestamp', 'latitude', 'longitude'])
            writer.writeheader()
            writer.writerow({'timestamp': '1.0', 'latitude': '37.1', 'longitude': '-122.1'})
            
        extractor = TelemetryExtractor(str(self.video_path))
        samples = extractor._read_external_telemetry()
        self.assertEqual(len(samples), 1)
        self.assertEqual(samples[0].latitude, 37.1)

    def test_json_compatibility(self):
        json_path = self.base_dir / "test_video_telemetry.json"
        json_path.write_text(json.dumps([{"timestamp": 1.0, "latitude": 37.2, "longitude": -122.2}]))
        
        extractor = TelemetryExtractor(str(self.video_path))
        samples = extractor._read_external_telemetry()
        self.assertEqual(len(samples), 1)
        self.assertEqual(samples[0].latitude, 37.2)

    def test_no_telemetry(self):
        extractor = TelemetryExtractor(str(self.video_path))
        samples = extractor._read_external_telemetry()
        self.assertEqual(len(samples), 0)

if __name__ == '__main__':
    unittest.main()
