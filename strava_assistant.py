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

from photo_processor import PhotoGeoTagger
from caption_generator import StravaCaptionGenerator

class StravaWorkflowHandler(FileSystemEventHandler):
    """Handles file system events for automatic processing."""
    
    def __init__(self, assistant):
        self.assistant = assistant
        self.processed_files = set()
        
    def on_created(self, event):
        if event.is_directory:
            return
            
        file_path = Path(event.src_path)
        
        # Check for new photos
        if file_path.suffix.lower() in ['.jpg', '.jpeg', '.png', '.heic']:
            print(f"New photo detected: {file_path}")
            time.sleep(2)  # Wait for file to be fully written
            self.assistant.queue_photo_for_processing(str(file_path))
            
        # Check for GPX files
        elif file_path.suffix.lower() == '.gpx':
            print(f"New GPX file detected: {file_path}")
            time.sleep(2)
            self.assistant.queue_gpx_for_processing(str(file_path))

class StravaAssistant:
    """Main class coordinating the Strava automation workflow."""
    
    def __init__(self, config: Dict):
        self.config = config
        self.photo_processor = PhotoGeoTagger(config.get('export_dir'))
        self.caption_generator = StravaCaptionGenerator()
        
        # Processing queues
        self.pending_photos = []
        self.pending_gpx = []
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
        
    def queue_gpx_for_processing(self, gpx_path: str):
        """Add GPX file to processing queue."""
        self.pending_gpx.append({
            'path': gpx_path,
            'timestamp': datetime.now(),
            'processed': False
        })
        self._try_process_pending()
        
    def _try_process_pending(self):
        """Try to process pending photos with available GPX data."""
        if not self.pending_photos or not self.pending_gpx:
            return
            
        # Group photos and GPX by time proximity
        sessions = self._group_files_by_session()
        
        for session in sessions:
            self._process_session(session)
            
    def _group_files_by_session(self, time_window_hours: int = 2) -> List[Dict]:
        """Group photos and GPX files by session based on timestamps."""
        sessions = []
        
        for gpx_entry in self.pending_gpx:
            if gpx_entry['processed']:
                continue
                
            session_photos = []
            gpx_time = gpx_entry['timestamp']
            
            for photo_entry in self.pending_photos:
                if photo_entry['processed']:
                    continue
                    
                photo_time = photo_entry['timestamp']
                time_diff = abs((photo_time - gpx_time).total_seconds()) / 3600
                
                if time_diff <= time_window_hours:
                    session_photos.append(photo_entry)
                    
            if session_photos:
                sessions.append({
                    'gpx': gpx_entry,
                    'photos': session_photos,
                    'session_id': f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                })
                
        return sessions
        
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
    
    # Watch command
    watch_parser = subparsers.add_parser('watch', help='Start watching directories for new files')
    watch_parser.add_argument('--photos', nargs='+', default=[str(Path.home() / 'Desktop')], 
                             help='Directories to watch for photos')
    watch_parser.add_argument('--gpx', nargs='+', default=[str(Path.home() / 'Downloads')], 
                             help='Directories to watch for GPX files')
    
    # Process command
    process_parser = subparsers.add_parser('process', help='Process specific files')
    process_parser.add_argument('photos_dir', help='Directory containing photos')
    process_parser.add_argument('gpx_file', help='GPX file path')
    
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
            print("🔍 Starting Strava Assistant file monitoring...")
            print("📸 Photo directories:", args.photos)
            print("🗺️ GPX directories:", args.gpx)
            print("Press Ctrl+C to stop")
            
            assistant.start_file_monitoring(args.photos + args.gpx)
            
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n⏹️ Stopping file monitoring...")
                assistant.stop_file_monitoring()
                
        elif args.command == 'process':
            print(f"📸 Processing photos from: {args.photos_dir}")
            print(f"🗺️ Using GPX file: {args.gpx_file}")
            
            # Manual processing
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