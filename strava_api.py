#!/usr/bin/env python3
"""
Improved Strava API with automatic token management
"""

import os
import json
import requests
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path
import tempfile
from dotenv import load_dotenv

load_dotenv()

class StravaAPI:
    """Client for interacting with Strava API v3 with auto token refresh."""
    
    def __init__(self):
        self.base_url = "https://www.strava.com/api/v3"
        self.client_id = os.getenv('STRAVA_CLIENT_ID')
        self.client_secret = os.getenv('STRAVA_CLIENT_SECRET')
        self.refresh_token = os.getenv('STRAVA_REFRESH_TOKEN')
        
        # Always get a fresh access token on startup
        self.access_token = self._get_fresh_access_token()
        
        if not self.access_token:
            raise ValueError("Failed to get valid access token")
    
    def _get_fresh_access_token(self) -> Optional[str]:
        """Always refresh the access token on startup."""
        if not self.refresh_token or not self.client_id or not self.client_secret:
            print("❌ Missing refresh token or client credentials in .env")
            return None
        
        print("🔄 Getting fresh access token...")
        
        token_url = "https://www.strava.com/oauth/token"
        data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'refresh_token': self.refresh_token,
            'grant_type': 'refresh_token'
        }
        
        try:
            response = requests.post(token_url, data=data)
            response.raise_for_status()
            token_data = response.json()
            
            # Update the refresh token (it might change)
            self.refresh_token = token_data['refresh_token']
            
            print("✅ Fresh access token obtained")
            return token_data['access_token']
            
        except Exception as e:
            print(f"❌ Failed to get fresh access token: {e}")
            return None
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers for API requests."""
        return {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
    
    def _make_request(self, endpoint: str, params: Dict = None) -> Dict:
        """Make authenticated request to Strava API."""
        url = f"{self.base_url}/{endpoint}"
        headers = self._get_headers()
        
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    
    def get_athlete_info(self) -> Dict:
        """Get authenticated athlete's basic info."""
        return self._make_request("athlete")
    
    def get_recent_activities(self, limit: int = 30, days_back: int = 7) -> List[Dict]:
        """Get recent activities for the authenticated athlete."""
        after_date = datetime.now() - timedelta(days=days_back)
        after_timestamp = int(after_date.timestamp())
        
        params = {
            'after': after_timestamp,
            'per_page': limit
        }
        
        activities = self._make_request("athlete/activities", params)
        
        # Filter for running activities only
        running_activities = [
            activity for activity in activities 
            if activity.get('sport_type', '').lower() in ['run', 'trailrun', 'virtualrun']
        ]
        
        print(f"✅ Found {len(running_activities)} running activities")
        return running_activities
    
    def get_activity_details(self, activity_id: int) -> Dict:
        """Get detailed information for a specific activity."""
        return self._make_request(f"activities/{activity_id}")
    
    def get_activity_streams(self, activity_id: int, stream_types: List[str] = None) -> Dict:
        """Get activity stream data (GPS coordinates, time, etc.)."""
        if stream_types is None:
            stream_types = ['latlng', 'time', 'altitude', 'distance']
        
        stream_types_str = ','.join(stream_types)
        endpoint = f"activities/{activity_id}/streams"
        params = {
            'keys': stream_types_str,
            'key_by_type': 'true'
        }
        
        return self._make_request(endpoint, params)
    
    def create_gpx_from_activity(self, activity_id: int, save_path: str = None) -> Optional[str]:
        """Create a GPX file from activity stream data."""
        try:
            # Get activity details and streams
            activity = self.get_activity_details(activity_id)
            streams = self.get_activity_streams(activity_id)
            
            if 'latlng' not in streams or 'time' not in streams:
                print(f"Activity {activity_id} missing required GPS or time data")
                return None
            
            # Extract data
            coordinates = streams['latlng']['data']  # List of [lat, lng] pairs
            time_data = streams['time']['data']      # List of seconds from start
            elevation_data = streams.get('altitude', {}).get('data', [])
            
            start_time = datetime.fromisoformat(activity['start_date_local'].replace('Z', '+00:00'))
            
            # Generate GPX content
            gpx_content = self._generate_gpx_content(
                coordinates, time_data, elevation_data, start_time, activity
            )
            
            # Save to file
            if save_path is None:
                save_path = tempfile.mktemp(suffix=f"_activity_{activity_id}.gpx")
            
            with open(save_path, 'w') as f:
                f.write(gpx_content)
            
            print(f"✓ GPX file created: {save_path}")
            return save_path
            
        except Exception as e:
            print(f"Error creating GPX from activity {activity_id}: {e}")
            return None
    
    def _generate_gpx_content(self, coordinates: List, time_data: List, 
                            elevation_data: List, start_time: datetime, 
                            activity: Dict) -> str:
        """Generate GPX XML content from stream data."""
        
        gpx_header = f'''<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" creator="StravaAssistant" 
     xsi:schemaLocation="http://www.topografix.com/GPX/1/1 http://www.topografix.com/GPX/1/1/gpx.xsd"
     xmlns="http://www.topografix.com/GPX/1/1" 
     xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <metadata>
    <name>{activity.get('name', 'Strava Activity')}</name>
    <desc>Generated from Strava activity {activity.get('id')}</desc>
    <time>{start_time.isoformat()}</time>
  </metadata>
  <trk>
    <name>{activity.get('name', 'Strava Activity')}</name>
    <type>{activity.get('sport_type', 'running')}</type>
    <trkseg>'''
        
        # Generate trackpoints
        trackpoints = []
        for i, (lat, lon) in enumerate(coordinates):
            if lat is None or lon is None:
                continue
            
            # Calculate timestamp for this point
            point_time = start_time + timedelta(seconds=time_data[i])
            time_str = point_time.isoformat()
            
            # Add elevation if available
            elevation_str = ""
            if i < len(elevation_data) and elevation_data[i] is not None:
                elevation_str = f"\n        <ele>{elevation_data[i]}</ele>"
            
            trackpoint = f'''
      <trkpt lat="{lat}" lon="{lon}">{elevation_str}
        <time>{time_str}</time>
      </trkpt>'''
            trackpoints.append(trackpoint)
        
        gpx_footer = '''
    </trkseg>
  </trk>
</gpx>'''
        
        return gpx_header + ''.join(trackpoints) + gpx_footer
    
    def get_activity_summary(self, activity: Dict) -> Dict:
        """Extract key information from activity for caption generation."""
        start_time = datetime.fromisoformat(activity['start_date_local'].replace('Z', '+00:00'))
        
        return {
            'activity_id': activity['id'],
            'name': activity['name'],
            'distance': activity['distance'],  # meters
            'moving_time': activity['moving_time'],  # seconds
            'elapsed_time': activity['elapsed_time'],  # seconds
            'total_elevation_gain': activity.get('total_elevation_gain', 0),
            'average_speed': activity.get('average_speed', 0) * 3.6,  # Convert m/s to km/h
            'start_date': start_time.isoformat(),
            'sport_type': activity.get('sport_type', 'Run'),
            'location': activity.get('location_city') or activity.get('location_state') or 'Unknown'
        }
    
    def get_activity_photos(self, activity_id: int) -> List[Dict]:
        """Get photos attached to an activity."""
        try:
            photos = self._make_request(f"activities/{activity_id}/photos")
            return photos
        except Exception as e:
            print(f"Error fetching photos for activity {activity_id}: {e}")
            return []
    
    def upload_activity_photo(self, activity_id: int, photo_path: str, caption: str = None) -> bool:
        """Upload a photo to an existing activity."""
        try:
            url = f"{self.base_url}/activities/{activity_id}/photos"
            headers = {'Authorization': f'Bearer {self.access_token}'}
            
            with open(photo_path, 'rb') as f:
                files = {'file': f}
                data = {'caption': caption} if caption else {}
                
                response = requests.post(url, headers=headers, files=files, data=data)
                response.raise_for_status()
                
            print(f"✓ Photo uploaded to activity {activity_id}")
            return True
            
        except Exception as e:
            print(f"Error uploading photo to activity {activity_id}: {e}")
            return False
    
    def create_activity(self, name: str, sport_type: str, start_date: str, 
                       elapsed_time: int, description: str = None, 
                       distance: float = None) -> Optional[Dict]:
        """Create a new activity on Strava."""
        try:
            url = f"{self.base_url}/activities"
            headers = self._get_headers()
            
            data = {
                'name': name,
                'type': sport_type,  # e.g., 'Run', 'Ride', 'Sail'
                'start_date_local': start_date,
                'elapsed_time': elapsed_time,
            }
            
            if description:
                data['description'] = description
            if distance:
                data['distance'] = distance
                
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            
            activity = response.json()
            print(f"✓ Created activity: {activity['name']} (ID: {activity['id']})")
            return activity
            
        except Exception as e:
            print(f"Error creating activity: {e}")
            return None
    
    def delete_activity(self, activity_id: int) -> bool:
        """Delete an activity from Strava."""
        try:
            url = f"{self.base_url}/activities/{activity_id}"
            headers = self._get_headers()
            
            response = requests.delete(url, headers=headers)
            response.raise_for_status()
            
            print(f"✓ Deleted activity {activity_id}")
            return True
            
        except Exception as e:
            print(f"Error deleting activity {activity_id}: {e}")
            return False
    
    def update_activity(self, activity_id: int, name: str = None, 
                       description: str = None, sport_type: str = None) -> bool:
        """Update an existing activity."""
        try:
            url = f"{self.base_url}/activities/{activity_id}"
            headers = self._get_headers()
            
            data = {}
            if name:
                data['name'] = name
            if description:
                data['description'] = description
            if sport_type:
                data['type'] = sport_type
                
            if not data:
                print("No update data provided")
                return False
                
            response = requests.put(url, headers=headers, json=data)
            response.raise_for_status()
            
            print(f"✓ Updated activity {activity_id}")
            return True
            
        except Exception as e:
            print(f"Error updating activity {activity_id}: {e}")
            return False

def test_strava_api():
    """Test function for Strava API integration."""
    try:
        api = StravaAPI()
        
        # Test athlete info
        athlete = api.get_athlete_info()
        print(f"✓ Connected as {athlete['firstname']} {athlete['lastname']}")
        
        # Test recent activities
        activities = api.get_recent_activities(limit=3)
        print(f"✓ Found {len(activities)} recent running activities")
        
        for activity in activities:
            summary = api.get_activity_summary(activity)
            print(f"  - {summary['name']}: {summary['distance']/1000:.1f}km")
        
        return True
        
    except Exception as e:
        print(f"✗ Strava API test failed: {e}")
        return False

if __name__ == '__main__':
    test_strava_api()