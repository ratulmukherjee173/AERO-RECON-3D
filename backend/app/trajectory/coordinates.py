import math
from typing import Tuple, Optional

class ENUConverter:
    """
    Foundation for converting WGS84 (Latitude, Longitude, Altitude) to 
    Local ENU (East, North, Up) Cartesian coordinates.
    
    Coordinate System: ENU
    Units: Meters
    Origin: Must be explicitly provided as a reference (lat, lon, alt)
    """
    
    # WGS84 Ellipsoid constants
    A = 6378137.0
    E_SQR = 0.00669437999014
    
    @staticmethod
    def wgs84_to_ecef(lat: float, lon: float, alt: float) -> Tuple[float, float, float]:
        """Convert WGS84 to Earth-Centered, Earth-Fixed (ECEF)."""
        lat_rad = math.radians(lat)
        lon_rad = math.radians(lon)
        
        n = ENUConverter.A / math.sqrt(1 - ENUConverter.E_SQR * math.sin(lat_rad)**2)
        x = (n + alt) * math.cos(lat_rad) * math.cos(lon_rad)
        y = (n + alt) * math.cos(lat_rad) * math.sin(lon_rad)
        z = (n * (1 - ENUConverter.E_SQR) + alt) * math.sin(lat_rad)
        return x, y, z

    @staticmethod
    def ecef_to_enu(x: float, y: float, z: float, 
                    lat0: float, lon0: float, alt0: float) -> Tuple[float, float, float]:
        """Convert ECEF to ENU given a reference origin."""
        x0, y0, z0 = ENUConverter.wgs84_to_ecef(lat0, lon0, alt0)
        
        dx = x - x0
        dy = y - y0
        dz = z - z0
        
        lat0_rad = math.radians(lat0)
        lon0_rad = math.radians(lon0)
        
        slat = math.sin(lat0_rad)
        clat = math.cos(lat0_rad)
        slon = math.sin(lon0_rad)
        clon = math.cos(lon0_rad)
        
        east = -slon * dx + clon * dy
        north = -slat * clon * dx - slat * slon * dy + clat * dz
        up = clat * clon * dx + clat * slon * dy + slat * dz
        
        return east, north, up

    @staticmethod
    def geodetic_to_enu(lat: float, lon: float, alt: float,
                        ref_lat: float, ref_lon: float, ref_alt: float) -> Tuple[float, float, float]:
        """
        Convert WGS84 coordinates to local ENU coordinates.
        Returns: (East, North, Up) in meters.
        """
        if any(v is None for v in [lat, lon, alt, ref_lat, ref_lon, ref_alt]):
            raise ValueError("Invalid coordinates for conversion.")
            
        x, y, z = ENUConverter.wgs84_to_ecef(lat, lon, alt)
        return ENUConverter.ecef_to_enu(x, y, z, ref_lat, ref_lon, ref_alt)

    @staticmethod
    def generate_enu_trajectory(samples: list) -> Tuple[list, Optional[Tuple[float, float, float]]]:
        """
        Converts a list of TelemetrySample objects into ENU MetricReferencePoint objects.
        Returns: (list of MetricReferencePoint, ENU origin (lat, lon, alt))
        """
        from ..telemetry.models import TelemetrySample
        from .models import MetricReferencePoint
        
        valid_samples = [s for s in samples if s.latitude is not None and s.longitude is not None and s.altitude is not None]
        
        if not valid_samples:
            return [], None
            
        # Use first valid sample as origin
        origin = (valid_samples[0].latitude, valid_samples[0].longitude, valid_samples[0].altitude)
        
        enu_points = []
        for s in samples:
            if s.latitude is None or s.longitude is None or s.altitude is None:
                continue
            
            try:
                east, north, up = ENUConverter.geodetic_to_enu(
                    s.latitude, s.longitude, s.altitude,
                    origin[0], origin[1], origin[2]
                )
                enu_points.append(
                    MetricReferencePoint(
                        timestamp=s.timestamp,
                        position=[east, north, up],
                        valid=True
                    )
                )
            except ValueError:
                continue
                
        return enu_points, origin
