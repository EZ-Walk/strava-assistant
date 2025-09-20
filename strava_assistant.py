#!/usr/bin/env python3
"""
Strava Assistant - Main Workflow Orchestrator
Coordinates photo processing, caption generation, and Strava posting.
"""

import os
import json
import time
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import argparse
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from photo_processor import PhotoGeoTagger
from caption_generator import StravaCaptionGenerator
from strava_api import StravaAPI

class StravaWorkflowHandler(FileSystemEventHandler):
    """Handles file system events for automatic processing."""
    
    def __init__(self, assistant):
        self.assistant = assistant
        self.processed_files = set()
        
    def on_created(self, event):
        if event.is_directory:
            return
            
        file_path = Path(event.src_path)
        
        # Check for new photos only (GPX files now come from Strava API)
        if file_path.suffix.lower() in ['.jpg', '.jpeg', '.png', '.heic']:
            print(f"New photo detected: {file_path}")
            time.sleep(2)  # Wait for file to be fully written
            self.assistant.queue_photo_for_processing(str(file_path))

class StravaAssistant:
    """Main class coordinating the Strava automation workflow."""
    
    def __init__(self, config: Dict):
        self.config = config
        self.photo_processor = PhotoGeoTagger(config.get('export_dir'))
        self.caption_generator = StravaCaptionGenerator()
        
        # Initialize Strava API
        try:
            self.strava_api = StravaAPI()
        except Exception as e:
            print(f"Warning: Strava API not available: {e}")
            self.strava_api = None
        
        # Processing queues
        self.pending_photos = []
        self.recent_activities = []  # Store recent activities from Strava
        self.processed_sessions = []
        
        # File watcher
        self.observer = None
        
        # Create working directories
        self.work_dir = Path(config.get('work_dir', Path.home() / 'strava-assistant'))
        self.work_dir.mkdir(exist_ok=True)
        
        (self.work_dir / 'pending').mkdir(exist_ok=True)
        (self.work_dir / 'processed').mkdir(exist_ok=True)
        (self.work_dir / 'sessions').mkdir(exist_ok=True)
        
    def start_file_monitoring(self, watch_dirs: List[str]):
        """Start monitoring directories for new photos and GPX files."""
        if self.observer:
            self.observer.stop()
            
        self.observer = Observer()
        handler = StravaWorkflowHandler(self)
        
        for watch_dir in watch_dirs:
            if os.path.exists(watch_dir):
                self.observer.schedule(handler, watch_dir, recursive=True)
                print(f"Monitoring {watch_dir} for new files...")
            else:
                print(f"Warning: Watch directory does not exist: {watch_dir}")
                
        self.observer.start()
        
    def stop_file_monitoring(self):
        """Stop file monitoring."""
        if self.observer:
            self.observer.stop()
            self.observer.join()
            
    def queue_photo_for_processing(self, photo_path: str):
        """Add photo to processing queue."""
        self.pending_photos.append({
            'path': photo_path,
            'timestamp': datetime.now(),
            'processed': False
        })
        self._try_process_pending()
        
    def fetch_recent_activities(self, days_back: int = 3):
        """Fetch recent activities from Strava API."""
        if not self.strava_api:
            print("Strava API not available")
            return
        
        try:
            activities = self.strava_api.get_recent_activities(days_back=days_back)
            print(f"Found {len(activities)} recent activities from Strava")
            
            for activity in activities:
                self.recent_activities.append({
                    'activity': activity,
                    'summary': self.strava_api.get_activity_summary(activity),
                    'processed': False
                })
            
            # Try to match with pending photos
            self._try_process_with_activities()
            
        except Exception as e:
            print(f"Error fetching Strava activities: {e}")
        
    def _try_process_with_activities(self):
        """Try to process pending photos with Strava activities."""
        if not self.pending_photos or not self.recent_activities:
            return
            
        # Group photos and activities by time proximity
        sessions = self._group_photos_with_activities()
        
        for session in sessions:
            self._process_session_with_activity(session)
            
    def _group_photos_with_activities(self, time_window_hours: int = 3) -> List[Dict]:
        """Group photos with Strava activities based on timestamps."""
        sessions = []
        
        for activity_entry in self.recent_activities:
            if activity_entry['processed']:
                continue
                
            activity_summary = activity_entry['summary']
            activity_time = datetime.fromisoformat(activity_summary['start_date'])
            
            session_photos = []
            
            for photo_entry in self.pending_photos:
                if photo_entry['processed']:
                    continue
                    
                photo_time = photo_entry['timestamp']
                time_diff = abs((photo_time - activity_time).total_seconds()) / 3600
                
                if time_diff <= time_window_hours:
                    session_photos.append(photo_entry)
                    
            if session_photos:
                sessions.append({
                    'activity': activity_entry,
                    'photos': session_photos,
                    'session_id': f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                })
                
        return sessions
        
    def _process_session_with_activity(self, session: Dict):
        """Process a session with photos and Strava activity data."""
        session_id = session['session_id']
        activity_entry = session['activity']
        photo_entries = session['photos']
        
        activity_summary = activity_entry['summary']
        activity_id = activity_summary['activity_id']
        
        print(f"\nProcessing session {session_id}")
        print(f"Strava activity: {activity_summary['name']} (ID: {activity_id})")
        print(f"Photos: {len(photo_entries)} files")
        
        # Create session directory
        session_dir = self.work_dir / 'sessions' / session_id
        session_dir.mkdir(exist_ok=True)
        
        # Create GPX file from Strava activity
        gpx_path = None
        if self.strava_api:
            try:
                gpx_path = self.strava_api.create_gpx_from_activity(
                    activity_id, 
                    str(session_dir / f"activity_{activity_id}.gpx")
                )
                print(f"✓ Created GPX from Strava activity: {gpx_path}")
            except Exception as e:
                print(f"Warning: Could not create GPX file: {e}")
        
        if not gpx_path:
            # Process without GPS data
            self._process_photos_without_gps(session_dir, photo_entries, activity_summary, session_id)
            return
        
        # Copy photos to session directory for processing
        photo_paths = []
        for photo_entry in photo_entries:
            original_path = Path(photo_entry['path'])
            session_photo_path = session_dir / original_path.name
            
            # Copy photo to session directory
            subprocess.run(['cp', str(original_path), str(session_photo_path)], check=True)
            photo_paths.append(str(session_photo_path))
            
        # Process photos with GPX data
        try:
            processed_photos = self.photo_processor.process_photos_with_gpx(
                str(session_dir), 
                gpx_path
            )
            
            if processed_photos:
                # Generate captions for each photo
                captions = []
                for photo_data in processed_photos:
                    caption = self.caption_generator.generate_caption(
                        activity_summary, 
                        photo_data,
                        include_sales_context=self.config.get('include_sales_context', False)
                    )
                    captions.append({
                        'photo_path': photo_data['photo_path'],
                        'caption': caption,
                        'photo_data': photo_data
                    })
                
                # Save session results
                session_results = {
                    'session_id': session_id,
                    'timestamp': datetime.now().isoformat(),
                    'strava_activity_id': activity_id,
                    'activity_data': activity_summary,
                    'processed_photos': processed_photos,
                    'captions': captions
                }
                
                results_file = session_dir / 'session_results.json'
                with open(results_file, 'w') as f:
                    json.dump(session_results, f, indent=2, default=str)
                
                print(f"✓ Session processed successfully!")
                print(f"✓ Results saved to: {results_file}")
                
                # Mark as processed
                activity_entry['processed'] = True
                for photo_entry in photo_entries:
                    photo_entry['processed'] = True
                    
                self.processed_sessions.append(session_results)
                
                # Display preview
                self._display_session_preview(session_results)
                
        except Exception as e:
            print(f"✗ Error processing session {session_id}: {e}")
    
    def _process_photos_without_gps(self, session_dir: Path, photo_entries: List, activity_summary: Dict, session_id: str):
        """Process photos when GPS data is not available."""
        print(f"Processing photos without GPS data for session {session_id}")
        
        # Copy photos and create basic data
        processed_photos = []
        for photo_entry in photo_entries:
            original_path = Path(photo_entry['path'])
            session_photo_path = session_dir / original_path.name
            
            # Copy photo to session directory
            subprocess.run(['cp', str(original_path), str(session_photo_path)], check=True)
            
            # Create basic photo data without GPS
            photo_data = {
                'photo_path': str(session_photo_path),
                'timestamp': photo_entry['timestamp'].isoformat(),
                'gps_data': {
                    'location_name': activity_summary.get('location', 'Unknown')
                },
                'photo_analysis': {}
            }
            processed_photos.append(photo_data)
        
        # Generate captions
        captions = []
        for photo_data in processed_photos:
            caption = self.caption_generator.generate_caption(
                activity_summary, 
                photo_data,
                include_sales_context=self.config.get('include_sales_context', False)
            )
            captions.append({
                'photo_path': photo_data['photo_path'],
                'caption': caption,
                'photo_data': photo_data
            })
        
        # Save session results
        session_results = {
            'session_id': session_id,
            'timestamp': datetime.now().isoformat(),
            'strava_activity_id': activity_summary['activity_id'],
            'activity_data': activity_summary,
            'processed_photos': processed_photos,
            'captions': captions,
            'note': 'Processed without GPS data'
        }
        
        results_file = session_dir / 'session_results.json'
        with open(results_file, 'w') as f:
            json.dump(session_results, f, indent=2, default=str)
        
        print(f"✓ Session processed (no GPS) successfully!")
        print(f"✓ Results saved to: {results_file}")
        
        self.processed_sessions.append(session_results)
        self._display_session_preview(session_results)
        
    def _process_session(self, session: Dict):
        """Process a complete session with photos and GPX data."""
        session_id = session['session_id']
        gpx_entry = session['gpx']
        photo_entries = session['photos']
        
        print(f"\nProcessing session {session_id}")
        print(f"GPX file: {gpx_entry['path']}")
        print(f"Photos: {len(photo_entries)} files")
        
        # Create session directory
        session_dir = self.work_dir / 'sessions' / session_id
        session_dir.mkdir(exist_ok=True)
        
        # Copy photos to session directory for processing
        photo_paths = []
        for photo_entry in photo_entries:
            original_path = Path(photo_entry['path'])
            session_photo_path = session_dir / original_path.name
            
            # Copy photo to session directory
            subprocess.run(['cp', str(original_path), str(session_photo_path)], check=True)
            photo_paths.append(str(session_photo_path))
            
        # Process photos with GPX data
        try:
            processed_photos = self.photo_processor.process_photos_with_gpx(
                str(session_dir), 
                gpx_entry['path']
            )
            
            if processed_photos:
                # Generate activity data from GPX
                activity_data = self._extract_activity_data(gpx_entry['path'])
                
                # Generate captions for each photo
                captions = []
                for photo_data in processed_photos:
                    caption = self.caption_generator.generate_caption(
                        activity_data, 
                        photo_data,
                        include_sales_context=self.config.get('include_sales_context', False)
                    )
                    captions.append({
                        'photo_path': photo_data['photo_path'],
                        'caption': caption,
                        'photo_data': photo_data
                    })
                
                # Save session results
                session_results = {
                    'session_id': session_id,
                    'timestamp': datetime.now().isoformat(),
                    'gpx_file': gpx_entry['path'],
                    'activity_data': activity_data,
                    'processed_photos': processed_photos,
                    'captions': captions
                }
                
                results_file = session_dir / 'session_results.json'
                with open(results_file, 'w') as f:
                    json.dump(session_results, f, indent=2, default=str)
                
                print(f"✓ Session processed successfully!")
                print(f"✓ Results saved to: {results_file}")
                
                # Mark files as processed
                gpx_entry['processed'] = True
                for photo_entry in photo_entries:
                    photo_entry['processed'] = True
                    
                self.processed_sessions.append(session_results)
                
                # Display preview
                self._display_session_preview(session_results)
                
        except Exception as e:
            print(f"✗ Error processing session {session_id}: {e}")
            
    def _extract_activity_data(self, gpx_path: str) -> Dict:
        """Extract activity metrics from GPX file."""
        try:
            trackpoints = self.photo_processor.parse_gpx_file(gpx_path)
            
            if not trackpoints:
                return {}
                
            # Calculate basic metrics
            total_distance = 0
            total_time = 0
            elevation_gain = 0
            speeds = []
            
            prev_point = None
            for point in trackpoints:
                if prev_point:
                    # Calculate distance between points
                    from geopy.distance import geodesic
                    dist = geodesic(
                        (prev_point['latitude'], prev_point['longitude']),
                        (point['latitude'], point['longitude'])
                    ).meters
                    total_distance += dist
                    
                    # Calculate time difference
                    time_diff = (point['time'] - prev_point['time']).total_seconds()
                    total_time += time_diff
                    
                    # Calculate speed
                    if time_diff > 0:
                        speed_ms = dist / time_diff
                        speed_kmh = speed_ms * 3.6
                        speeds.append(speed_kmh)
                    
                    # Calculate elevation gain
                    if point['elevation'] and prev_point['elevation']:
                        elev_diff = point['elevation'] - prev_point['elevation']
                        if elev_diff > 0:
                            elevation_gain += elev_diff
                            
                prev_point = point
                
            # Calculate averages
            avg_speed = sum(speeds) / len(speeds) if speeds else 0
            
            return {
                'distance': total_distance,  # meters
                'duration': total_time,  # seconds
                'average_speed': avg_speed,  # km/h
                'elevation_gain': elevation_gain,  # meters
                'start_time': trackpoints[0]['time'].isoformat() if trackpoints else None,
                'end_time': trackpoints[-1]['time'].isoformat() if trackpoints else None
            }
            
        except Exception as e:
            print(f"Error extracting activity data from {gpx_path}: {e}")
            return {}
            
    def _display_session_preview(self, session_results: Dict):
        """Display a preview of the processed session."""
        print("\n" + "="*60)
        print(f"SESSION PREVIEW: {session_results['session_id']}")
        print("="*60)
        
        activity_data = session_results['activity_data']
        distance_km = activity_data.get('distance', 0) / 1000
        duration_min = activity_data.get('duration', 0) / 60
        avg_speed = activity_data.get('average_speed', 0)
        elevation = activity_data.get('elevation_gain', 0)
        
        print(f"📊 Activity: {distance_km:.1f}km in {duration_min:.0f}min")
        print(f"⚡ Avg Speed: {avg_speed:.1f} km/h")
        print(f"📈 Elevation: {elevation:.0f}m gain")
        print(f"📸 Photos: {len(session_results['captions'])}")
        
        print("\n📝 Generated Captions:")
        for i, caption_data in enumerate(session_results['captions'], 1):
            photo_name = Path(caption_data['photo_path']).name
            print(f"\n{i}. {photo_name}")
            print(f"   {caption_data['caption']}")
            
        print("\n" + "="*60)
        print("Ready to post to Strava! Run 'strava_assistant.py post <session_id>' to upload.")
        print("="*60)
        
    def post_session_to_strava(self, session_id: str):
        """Post a processed session to Strava (requires MCP setup)."""
        session_file = self.work_dir / 'sessions' / session_id / 'session_results.json'
        
        if not session_file.exists():
            print(f"Session not found: {session_id}")
            return False
            
        with open(session_file, 'r') as f:
            session_data = json.load(f)
            
        print(f"Posting session {session_id} to Strava...")
        
        # This would integrate with the Strava MCP server
        # For now, just show what would be posted
        print("🚀 Would post to Strava:")
        for caption_data in session_data['captions']:
            print(f"📸 {Path(caption_data['photo_path']).name}")
            print(f"📝 {caption_data['caption']}")
            print()
            
        print("✅ Session ready for Strava! (MCP integration needed)")
        return True
        
    def list_sessions(self):
        """List all processed sessions."""
        sessions_dir = self.work_dir / 'sessions'
        sessions = []
        
        for session_dir in sessions_dir.iterdir():
            if session_dir.is_dir():
                results_file = session_dir / 'session_results.json'
                if results_file.exists():
                    with open(results_file, 'r') as f:
                        session_data = json.load(f)
                    sessions.append(session_data)
                    
        return sorted(sessions, key=lambda x: x['timestamp'], reverse=True)

def main():
    """Main CLI interface."""
    parser = argparse.ArgumentParser(description='Strava Assistant - Automate your running posts')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Watch command - now monitors photos and fetches activities from Strava
    watch_parser = subparsers.add_parser('watch', help='Monitor photos and fetch Strava activities')
    watch_parser.add_argument('--photos', nargs='+', default=[str(Path.home() / 'Desktop'), str(Path.home() / 'Downloads')], 
                             help='Directories to watch for photos')
    watch_parser.add_argument('--days', type=int, default=3, 
                             help='Number of days back to fetch Strava activities')
    
    # Process command
    process_parser = subparsers.add_parser('process', help='Process specific files')
    process_parser.add_argument('photos_dir', help='Directory containing photos')
    process_parser.add_argument('gpx_file', nargs='?', help='GPX file path (optional - will fetch from Strava if not provided)')
    
    # Fetch command - new command to get recent activities
    fetch_parser = subparsers.add_parser('fetch', help='Fetch recent activities from Strava')
    fetch_parser.add_argument('--days', type=int, default=7, 
                             help='Number of days back to fetch activities')
    
    # Post command
    post_parser = subparsers.add_parser('post', help='Post session to Strava')
    post_parser.add_argument('session_id', help='Session ID to post')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List processed sessions')
    
    args = parser.parse_args()
    
    # Load configuration
    config = {
        'work_dir': str(Path.home() / 'strava-assistant'),
        'export_dir': str(Path.home() / 'strava-processed'),
        'include_sales_context': True  # Enable sales context in captions
    }
    
    assistant = StravaAssistant(config)
    
    try:
        if args.command == 'watch':
            print("🔍 Starting Strava Assistant with photo monitoring and Strava integration...")
            print("📸 Photo directories:", args.photos)
            print(f"📊 Fetching Strava activities from last {args.days} days")
            print("Press Ctrl+C to stop")
            
            # Fetch recent activities from Strava
            assistant.fetch_recent_activities(days_back=args.days)
            
            # Start monitoring photos only
            assistant.start_file_monitoring(args.photos)
            
            try:
                while True:
                    time.sleep(10)  # Check every 10 seconds
                    # Periodically fetch new activities
                    assistant.fetch_recent_activities(days_back=args.days)
            except KeyboardInterrupt:
                print("\n⏹️ Stopping file monitoring...")
                assistant.stop_file_monitoring()
                
        elif args.command == 'process':
            print(f"📸 Processing photos from: {args.photos_dir}")
            
            if args.gpx_file:
                print(f"🗺️ Using GPX file: {args.gpx_file}")
                # Manual processing with GPX file
                processed_photos = assistant.photo_processor.process_photos_with_gpx(
                    args.photos_dir, args.gpx_file
                )
                
                if processed_photos:
                    activity_data = assistant._extract_activity_data(args.gpx_file)
                    
                    for photo_data in processed_photos:
                        caption = assistant.caption_generator.generate_caption(
                            activity_data, photo_data, include_sales_context=True
                        )
                        print(f"\n📸 {Path(photo_data['photo_path']).name}")
                        print(f"📝 {caption}")
            else:
                print("🗺️ No GPX file provided - will attempt to match with recent Strava activities")
                # Fetch recent activities and try to match
                assistant.fetch_recent_activities(days_back=7)
                
                # Queue photos for processing
                photo_dir = Path(args.photos_dir)
                for photo_path in photo_dir.glob('*.[jJ][pP][gG]'):
                    assistant.queue_photo_for_processing(str(photo_path))
                for photo_path in photo_dir.glob('*.[jJ][pP][eE][gG]'):
                    assistant.queue_photo_for_processing(str(photo_path))
                for photo_path in photo_dir.glob('*.[pP][nN][gG]'):
                    assistant.queue_photo_for_processing(str(photo_path))
                for photo_path in photo_dir.glob('*.[hH][eE][iI][cC]'):
                    assistant.queue_photo_for_processing(str(photo_path))
        
        elif args.command == 'fetch':
            print(f"📊 Fetching recent activities from Strava ({args.days} days back)...")
            assistant.fetch_recent_activities(days_back=args.days)
                    
        elif args.command == 'post':
            assistant.post_session_to_strava(args.session_id)
            
        elif args.command == 'list':
            sessions = assistant.list_sessions()
            if sessions:
                print("📋 Processed Sessions:")
                for session in sessions:
                    print(f"  🆔 {session['session_id']}")
                    print(f"     📅 {session['timestamp'][:19]}")
                    print(f"     📸 {len(session['captions'])} photos")
                    print()
            else:
                print("📭 No processed sessions found")
                
        else:
            parser.print_help()
            
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
        assistant.stop_file_monitoring()

if __name__ == '__main__':
    main()