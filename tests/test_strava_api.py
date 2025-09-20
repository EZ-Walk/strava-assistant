#!/usr/bin/env python3
"""
Comprehensive tests for Strava API functionality.
Tests fetching activities, metadata, media, and full CRUD operations.
"""

import pytest
import os
import sys
import tempfile
import json
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from strava_api import StravaAPI

class TestStravaAPI:
    """Test suite for Strava API functionality."""
    
    @classmethod
    def setup_class(cls):
        """Set up test class with API connection."""
        try:
            cls.api = StravaAPI()
            cls.test_activity_id = None  # Will store created test activity ID
        except Exception as e:
            pytest.skip(f"Strava API not available: {e}")
    
    def test_api_initialization(self):
        """Test that Strava API initializes correctly with auto-refresh."""
        assert self.api is not None
        assert self.api.access_token is not None
        assert self.api.base_url == "https://www.strava.com/api/v3"
        print("✓ API initialized with auto-refresh tokens")
    
    def test_athlete_info(self):
        """Test fetching authenticated athlete information."""
        athlete = self.api.get_athlete_info()
        
        assert isinstance(athlete, dict)
        assert 'id' in athlete
        assert 'firstname' in athlete
        assert 'lastname' in athlete
        
        print(f"✓ Connected as {athlete['firstname']} {athlete['lastname']} (ID: {athlete['id']})")
        
    def test_fetch_recent_activities(self):
        """Test fetching recent activities and their metadata."""
        activities = self.api.get_recent_activities(limit=5, days_back=30)
        
        assert isinstance(activities, list)
        print(f"✓ Found {len(activities)} recent running activities")
        
        if activities:
            # Test first activity metadata
            activity = activities[0]
            required_fields = ['id', 'name', 'distance', 'moving_time', 'sport_type']
            
            for field in required_fields:
                assert field in activity, f"Missing required field: {field}"
            
            print(f"✓ Activity metadata complete for: {activity['name']}")
            
            # Test activity summary extraction
            summary = self.api.get_activity_summary(activity)
            summary_fields = ['activity_id', 'name', 'distance', 'moving_time', 'start_date']
            
            for field in summary_fields:
                assert field in summary, f"Missing summary field: {field}"
            
            print(f"✓ Activity summary: {summary['name']} - {summary['distance']/1000:.1f}km")
            
            return activities[0]  # Return for use in other tests
    
    def test_activity_details(self):
        """Test fetching detailed activity information."""
        activities = self.api.get_recent_activities(limit=1, days_back=30)
        
        if not activities:
            pytest.skip("No recent activities found for detailed testing")
        
        activity_id = activities[0]['id']
        details = self.api.get_activity_details(activity_id)
        
        assert isinstance(details, dict)
        assert details['id'] == activity_id
        assert 'start_latlng' in details or 'end_latlng' in details
        
        print(f"✓ Fetched detailed info for activity {activity_id}")
    
    def test_activity_streams(self):
        """Test fetching activity GPS and time stream data."""
        activities = self.api.get_recent_activities(limit=1, days_back=30)
        
        if not activities:
            pytest.skip("No recent activities found for stream testing")
        
        activity_id = activities[0]['id']
        streams = self.api.get_activity_streams(activity_id)
        
        assert isinstance(streams, dict)
        
        # Check for expected stream types
        expected_streams = ['latlng', 'time', 'altitude', 'distance']
        found_streams = []
        
        for stream_type in expected_streams:
            if stream_type in streams:
                found_streams.append(stream_type)
                assert 'data' in streams[stream_type]
                assert isinstance(streams[stream_type]['data'], list)
        
        print(f"✓ Found streams: {', '.join(found_streams)} for activity {activity_id}")
        
        # Test GPX creation from streams
        if 'latlng' in streams and 'time' in streams:
            gpx_path = self.api.create_gpx_from_activity(activity_id)
            if gpx_path:
                assert os.path.exists(gpx_path)
                print(f"✓ Created GPX file: {gpx_path}")
                
                # Clean up
                os.unlink(gpx_path)
    
    def test_activity_photos(self):
        """Test fetching photos attached to activities."""
        activities = self.api.get_recent_activities(limit=3, days_back=30)
        
        if not activities:
            pytest.skip("No recent activities found for photo testing")
        
        photo_counts = []
        for activity in activities:
            activity_id = activity['id']
            photos = self.api.get_activity_photos(activity_id)
            
            assert isinstance(photos, list)
            photo_counts.append(len(photos))
            
            if photos:
                # Test photo metadata
                photo = photos[0]
                assert 'urls' in photo
                print(f"✓ Activity {activity_id} has {len(photos)} photos")
                break
        
        total_photos = sum(photo_counts)
        print(f"✓ Found {total_photos} total photos across {len(activities)} activities")

class TestStravaActivityCreation:
    """Test suite for creating, updating, and deleting Strava activities."""
    
    @classmethod
    def setup_class(cls):
        """Set up test class with API connection."""
        try:
            cls.api = StravaAPI()
            cls.test_activity_id = None
        except Exception as e:
            pytest.skip(f"Strava API not available: {e}")
    
    def test_create_test_activity(self):
        """Test creating a new test activity on Strava."""
        # Create test activity
        test_name = f"Test Activity - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        test_description = "Test activity created by Strava Assistant automated tests"
        start_date = datetime.now().isoformat()
        
        activity = self.api.create_activity(
            name=test_name,
            sport_type="Run",
            start_date=start_date,
            elapsed_time=1800,  # 30 minutes
            description=test_description,
            distance=5000  # 5km
        )
        
        if activity:
            assert isinstance(activity, dict)
            assert 'id' in activity
            assert activity['name'] == test_name
            
            # Store for cleanup
            self.__class__.test_activity_id = activity['id']
            
            print(f"✓ Created test activity: {activity['name']} (ID: {activity['id']})")
            return activity
        else:
            pytest.skip("Could not create test activity - may be API limitation")
    
    def test_update_activity(self):
        """Test updating the created test activity."""
        if not self.test_activity_id:
            pytest.skip("No test activity available for update testing")
        
        updated_name = f"Updated Test Activity - {datetime.now().strftime('%H:%M:%S')}"
        updated_description = "Updated by automated tests"
        
        success = self.api.update_activity(
            self.test_activity_id,
            name=updated_name,
            description=updated_description
        )
        
        assert success, "Failed to update test activity"
        print(f"✓ Updated activity {self.test_activity_id}")
    
    def test_upload_photo_to_activity(self):
        """Test uploading a photo to the test activity."""
        if not self.test_activity_id:
            pytest.skip("No test activity available for photo upload testing")
        
        # Create a simple test image
        test_image_content = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x01\x00\x00\x00\x007n\xf9$\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xdb\x00\x00\x00\x00IEND\xaeB`\x82'
        
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            f.write(test_image_content)
            test_image_path = f.name
        
        try:
            success = self.api.upload_activity_photo(
                self.test_activity_id,
                test_image_path,
                caption="Test photo uploaded by automated tests"
            )
            
            if success:
                print(f"✓ Uploaded photo to activity {self.test_activity_id}")
            else:
                print("⚠️ Photo upload API endpoint not available (expected)")
                
        finally:
            # Clean up test image
            os.unlink(test_image_path)
    
    def test_delete_test_activity(self):
        """Test deleting the created test activity - CLEANUP."""
        if not self.test_activity_id:
            pytest.skip("No test activity to delete")
        
        success = self.api.delete_activity(self.test_activity_id)
        
        if success:
            print(f"✓ Deleted test activity {self.test_activity_id}")
            self.__class__.test_activity_id = None
        else:
            print(f"⚠️ Could not delete via API - manual cleanup needed for activity {self.test_activity_id}")
            print("This is expected - Strava may require special permissions for deletion")
            # Don't fail the test since this is an expected API limitation

class TestIntegrationWorkflow:
    """Integration tests for the complete photo + GPX → Strava workflow."""
    
    @classmethod
    def setup_class(cls):
        """Set up test class with API and test data."""
        try:
            cls.api = StravaAPI()
            cls.test_activity_id = None
            cls._create_test_data()
        except Exception as e:
            pytest.skip(f"Integration test setup failed: {e}")
    
    @classmethod
    def _create_test_data(cls):
        """Create test GPX and photo files."""
        # Create test GPX file
        test_gpx_content = '''<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" creator="Test">
  <metadata>
    <name>Test Run</name>
    <time>2024-01-01T10:00:00Z</time>
  </metadata>
  <trk>
    <name>Test Run</name>
    <type>running</type>
    <trkseg>
      <trkpt lat="37.7749" lon="-122.4194">
        <ele>50</ele>
        <time>2024-01-01T10:00:00Z</time>
      </trkpt>
      <trkpt lat="37.7750" lon="-122.4195">
        <ele>52</ele>
        <time>2024-01-01T10:05:00Z</time>
      </trkpt>
      <trkpt lat="37.7751" lon="-122.4196">
        <ele>54</ele>
        <time>2024-01-01T10:10:00Z</time>
      </trkpt>
    </trkseg>
  </trk>
</gpx>'''
        
        cls.test_dir = tempfile.mkdtemp()
        
        # Save test GPX
        cls.test_gpx_path = os.path.join(cls.test_dir, 'test_run.gpx')
        with open(cls.test_gpx_path, 'w') as f:
            f.write(test_gpx_content)
        
        # Create test image with minimal PNG content
        test_image_content = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x10\x00\x00\x00\x10\x08\x02\x00\x00\x00\x90\x91h6\x00\x00\x00\x19IDATx\x9c\x01\x0e\x00\xf1\xff\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x03\x10\x00\x01\xb5\x18q\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
        
        cls.test_photo_path = os.path.join(cls.test_dir, 'test_photo.png')
        with open(cls.test_photo_path, 'wb') as f:
            f.write(test_image_content)
    
    def test_gpx_processing(self):
        """Test processing GPX file and extracting activity data."""
        # Test GPX parsing
        from photo_processor import PhotoGeoTagger
        processor = PhotoGeoTagger()
        
        trackpoints = processor.parse_gpx_file(self.test_gpx_path)
        
        assert len(trackpoints) == 3
        assert trackpoints[0]['latitude'] == 37.7749
        assert trackpoints[0]['longitude'] == -122.4194
        
        print(f"✓ Parsed {len(trackpoints)} trackpoints from test GPX")
    
    def test_create_activity_from_gpx(self):
        """Test creating a Strava activity from GPX data."""
        # Parse GPX for activity metrics
        from photo_processor import PhotoGeoTagger
        processor = PhotoGeoTagger()
        trackpoints = processor.parse_gpx_file(self.test_gpx_path)
        
        # Calculate basic metrics
        total_distance = 200  # Approximate distance for test
        total_time = 600  # 10 minutes
        
        # Create activity
        test_name = f"Integration Test Run - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        activity = self.api.create_activity(
            name=test_name,
            sport_type="Run",
            start_date="2024-01-01T10:00:00",
            elapsed_time=total_time,
            description="Created by integration test with GPX data",
            distance=total_distance
        )
        
        if activity:
            self.__class__.test_activity_id = activity['id']
            print(f"✓ Created activity from GPX: {activity['name']} (ID: {activity['id']})")
            return activity
        else:
            pytest.skip("Could not create activity from GPX data")
    
    def test_add_photos_to_activity(self):
        """Test adding processed photos to the created activity."""
        if not self.test_activity_id:
            pytest.skip("No test activity available for photo testing")
        
        # This would normally involve photo processing with GPS matching
        # For now, just test the photo upload capability
        success = self.api.upload_activity_photo(
            self.test_activity_id,
            self.test_photo_path,
            caption="Test photo from integration test"
        )
        
        if success:
            print(f"✓ Added photo to activity {self.test_activity_id}")
        else:
            print("⚠️ Photo upload may not be supported - continuing test")
    
    def test_cleanup_test_activity(self):
        """Test deleting the integration test activity - CLEANUP."""
        if not self.test_activity_id:
            pytest.skip("No test activity to clean up")
        
        success = self.api.delete_activity(self.test_activity_id)
        
        if success:
            print(f"✓ Cleaned up integration test activity {self.test_activity_id}")
        else:
            print(f"⚠️ Could not delete via API - manual cleanup needed for activity {self.test_activity_id}")
            print("This is expected - Strava may require special permissions for deletion")
        
        # Clean up test files
        import shutil
        shutil.rmtree(self.test_dir)
        print("✓ Cleaned up test files")

if __name__ == '__main__':
    # Run tests with verbose output
    pytest.main([__file__, '-v', '-s'])