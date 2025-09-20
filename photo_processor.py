#!/usr/bin/env python3
"""
Photo Processing and Geotagging Pipeline
Automatically processes running photos and matches them with GPX data.
"""

import os
import json
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import gpxpy
from PIL import Image
from PIL.ExifTags import TAGS
import exifread
from geopy.geocoders import Nominatim
import time

class PhotoGeoTagger:
    """Handles photo geotagging using GPX data and EXIF timestamps."""
    
    def __init__(self, export_dir: str = None):
        self.export_dir = Path(export_dir) if export_dir else Path.home() / "strava-processed"
        self.export_dir.mkdir(exist_ok=True)
        self.geolocator = Nominatim(user_agent="strava-assistant")
        
    def extract_photo_timestamp(self, photo_path: str) -> Optional[datetime]:
        """Extract timestamp from photo EXIF data."""
        try:
            with open(photo_path, 'rb') as f:
                tags = exifread.process_file(f, stop_tag='EXIF DateTimeOriginal')
                
            if 'EXIF DateTimeOriginal' in tags:
                timestamp_str = str(tags['EXIF DateTimeOriginal'])
                return datetime.strptime(timestamp_str, '%Y:%m:%d %H:%M:%S')
            elif 'Image DateTime' in tags:
                timestamp_str = str(tags['Image DateTime'])
                return datetime.strptime(timestamp_str, '%Y:%m:%d %H:%M:%S')
                
        except Exception as e:
            print(f"Error extracting timestamp from {photo_path}: {e}")
            
        # Fallback to file modification time
        try:
            stat = os.stat(photo_path)
            return datetime.fromtimestamp(stat.st_mtime)
        except:
            return None
    
    def parse_gpx_file(self, gpx_path: str) -> List[Dict]:
        """Parse GPX file and return list of trackpoints with timestamps."""
        trackpoints = []
        
        try:
            with open(gpx_path, 'r') as gpx_file:
                gpx = gpxpy.parse(gpx_file)
                
            for track in gpx.tracks:
                for segment in track.segments:
                    for point in segment.points:
                        if point.time:
                            trackpoints.append({
                                'latitude': point.latitude,
                                'longitude': point.longitude,
                                'elevation': point.elevation,
                                'time': point.time,
                                'speed': getattr(point, 'speed', None)
                            })
                            
        except Exception as e:
            print(f"Error parsing GPX file {gpx_path}: {e}")
            
        return sorted(trackpoints, key=lambda x: x['time'])
    
    def find_closest_trackpoint(self, photo_timestamp: datetime, trackpoints: List[Dict], 
                               tolerance_seconds: int = 30) -> Optional[Dict]:
        """Find the closest GPX trackpoint to the photo timestamp."""
        if not trackpoints:
            return None
            
        closest_point = None
        min_diff = float('inf')
        
        for point in trackpoints:
            # Convert GPX time to local time if needed
            gpx_time = point['time']
            if gpx_time.tzinfo is not None:
                gpx_time = gpx_time.replace(tzinfo=None)
                
            time_diff = abs((photo_timestamp - gpx_time).total_seconds())
            
            if time_diff < min_diff and time_diff <= tolerance_seconds:
                min_diff = time_diff
                closest_point = point
                
        return closest_point
    
    def get_location_name(self, latitude: float, longitude: float) -> str:
        """Get human-readable location name from coordinates."""
        try:
            location = self.geolocator.reverse((latitude, longitude), timeout=10)
            if location:
                address = location.raw.get('address', {})
                # Extract relevant location components
                components = []
                for key in ['neighbourhood', 'suburb', 'city', 'town', 'village']:
                    if key in address:
                        components.append(address[key])
                        break
                        
                if 'state' in address:
                    components.append(address['state'])
                    
                return ', '.join(components) if components else str(location.address)
            
        except Exception as e:
            print(f"Error getting location name for {latitude}, {longitude}: {e}")
            
        return f"{latitude:.4f}, {longitude:.4f}"
    
    def geotag_photo(self, photo_path: str, latitude: float, longitude: float, 
                     elevation: float = None) -> bool:
        """Add GPS coordinates to photo EXIF data using exiftool."""
        try:
            cmd = ['exiftool', '-overwrite_original']
            cmd.extend([f'-GPS:GPSLatitude={latitude}'])
            cmd.extend([f'-GPS:GPSLongitude={longitude}'])
            
            if elevation is not None:
                cmd.extend([f'-GPS:GPSAltitude={elevation}'])
                
            cmd.append(photo_path)
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"Error geotagging {photo_path}: {e}")
            return False
        except FileNotFoundError:
            print("exiftool not found. Please install it: brew install exiftool")
            return False
    
    def analyze_photo_content(self, photo_path: str) -> Dict:
        """Analyze photo content for caption generation."""
        try:
            with Image.open(photo_path) as img:
                # Basic image analysis
                analysis = {
                    'size': img.size,
                    'mode': img.mode,
                    'format': img.format,
                    'orientation': 'landscape' if img.size[0] > img.size[1] else 'portrait'
                }
                
                # Extract additional EXIF data
                exif_data = img._getexif()
                if exif_data:
                    for tag_id in exif_data:
                        tag = TAGS.get(tag_id, tag_id)
                        if tag in ['Make', 'Model', 'LensModel', 'FocalLength', 'ISO']:
                            analysis[tag.lower()] = exif_data[tag_id]
                            
                return analysis
                
        except Exception as e:
            print(f"Error analyzing photo {photo_path}: {e}")
            return {}
    
    def process_photos_with_gpx(self, photo_dir: str, gpx_path: str) -> List[Dict]:
        """Process all photos in directory with GPX data."""
        photo_dir = Path(photo_dir)
        processed_photos = []
        
        print(f"Processing photos from {photo_dir} with GPX data from {gpx_path}")
        
        # Parse GPX data
        trackpoints = self.parse_gpx_file(gpx_path)
        if not trackpoints:
            print("No trackpoints found in GPX file")
            return []
            
        print(f"Found {len(trackpoints)} trackpoints in GPX file")
        
        # Process each photo
        for photo_path in photo_dir.glob('*.{jpg,jpeg,png,heic}'):
            if not photo_path.is_file():
                continue
                
            print(f"Processing {photo_path.name}...")
            
            # Extract photo timestamp
            photo_timestamp = self.extract_photo_timestamp(str(photo_path))
            if not photo_timestamp:
                print(f"Could not extract timestamp from {photo_path.name}")
                continue
                
            # Find closest GPX point
            closest_point = self.find_closest_trackpoint(photo_timestamp, trackpoints)
            if not closest_point:
                print(f"No matching GPX point found for {photo_path.name}")
                continue
                
            # Geotag the photo
            if self.geotag_photo(str(photo_path), 
                               closest_point['latitude'], 
                               closest_point['longitude'], 
                               closest_point['elevation']):
                
                # Get location name
                location_name = self.get_location_name(
                    closest_point['latitude'], 
                    closest_point['longitude']
                )
                
                # Analyze photo content
                photo_analysis = self.analyze_photo_content(str(photo_path))
                
                processed_data = {
                    'photo_path': str(photo_path),
                    'timestamp': photo_timestamp.isoformat(),
                    'gps_data': {
                        'latitude': closest_point['latitude'],
                        'longitude': closest_point['longitude'],
                        'elevation': closest_point['elevation'],
                        'location_name': location_name
                    },
                    'photo_analysis': photo_analysis,
                    'time_diff_seconds': abs((photo_timestamp - closest_point['time']).total_seconds())
                }
                
                processed_photos.append(processed_data)
                print(f"✓ Geotagged {photo_path.name} at {location_name}")
                
            else:
                print(f"✗ Failed to geotag {photo_path.name}")
                
        return processed_photos

def main():
    """Example usage of the PhotoGeoTagger."""
    import sys
    
    if len(sys.argv) != 3:
        print("Usage: python photo_processor.py <photo_directory> <gpx_file>")
        sys.exit(1)
        
    photo_dir = sys.argv[1]
    gpx_file = sys.argv[2]
    
    if not os.path.exists(photo_dir):
        print(f"Photo directory does not exist: {photo_dir}")
        sys.exit(1)
        
    if not os.path.exists(gpx_file):
        print(f"GPX file does not exist: {gpx_file}")
        sys.exit(1)
    
    tagger = PhotoGeoTagger()
    processed_photos = tagger.process_photos_with_gpx(photo_dir, gpx_file)
    
    # Save processing results
    results_file = Path.home() / "strava-processed" / f"processed_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_file, 'w') as f:
        json.dump(processed_photos, f, indent=2, default=str)
        
    print(f"\nProcessing complete!")
    print(f"Processed {len(processed_photos)} photos")
    print(f"Results saved to: {results_file}")

if __name__ == '__main__':
    main()