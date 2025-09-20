#!/usr/bin/env python3
"""
AI Caption Generation System
Generates engaging Strava captions using photo analysis and running data.
"""

import json
import re
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path
import random

class StravaCaptionGenerator:
    """Generates personalized Strava captions from photo and activity data."""
    
    def __init__(self):
        self.templates = self._load_caption_templates()
        self.emoji_map = {
            'running': ['🏃‍♂️', '👟', '💨', '🏃‍♀️'],
            'scenery': ['🌲', '🏔️', '🌅', '🌄', '🌊', '🏞️'],
            'weather': {
                'sunny': ['☀️', '🌞'],
                'cloudy': ['☁️', '⛅'],
                'rainy': ['🌧️', '☔'],
                'cold': ['🥶', '❄️'],
                'hot': ['🔥', '🥵']
            },
            'achievement': ['💪', '🎯', '🔥', '⚡', '🚀'],
            'tired': ['😅', '💦', '🫠'],
            'happy': ['😄', '😊', '🤗'],
            'location': ['📍', '🗺️']
        }
        
    def _load_caption_templates(self) -> Dict:
        """Load caption templates for different scenarios."""
        return {
            'morning_run': [
                "Started the day right with a {distance} run through {location}! {weather_desc}",
                "Morning miles in {location} - {distance} of pure {mood}! {achievement}",
                "Early bird gets the {distance}! Beautiful morning in {location}"
            ],
            'evening_run': [
                "Perfect way to end the day - {distance} through {location}",
                "Evening therapy session: {distance} in {location} {weather_desc}",
                "Chasing the sunset for {distance} in {location}"
            ],
            'scenic_run': [
                "When your running route looks like this, you know you're doing something right! {distance} in {location}",
                "Sometimes you run for fitness, sometimes for views like this. {distance} well spent in {location}",
                "Nature's gym > regular gym. {distance} of pure beauty in {location}"
            ],
            'challenging_run': [
                "That was tough but so worth it! {distance} of hills and determination in {location}",
                "Legs are tired, spirit is strong. {distance} conquered in {location}",
                "Every hill was worth this view. {distance} of character building in {location}"
            ],
            'casual_run': [
                "Easy {distance} through {location} - sometimes it's about the journey, not the pace",
                "Recovery run vibes in {location}. {distance} of zen",
                "Just me, {distance}, and the beautiful {location} scenery"
            ],
            'sales_context': [
                "Post-meeting run therapy - {distance} in {location} to clear the head",
                "Nothing like a good run to process the day's conversations. {distance} in {location}",
                "From boardroom to {location} - {distance} of decompression"
            ]
        }
    
    def analyze_time_of_day(self, timestamp: str) -> str:
        """Determine time of day from timestamp."""
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            hour = dt.hour
            
            if 5 <= hour < 11:
                return 'morning'
            elif 11 <= hour < 17:
                return 'afternoon'
            elif 17 <= hour < 21:
                return 'evening'
            else:
                return 'night'
        except:
            return 'day'
    
    def determine_run_type(self, activity_data: Dict, photo_data: Dict) -> str:
        """Determine the type of run based on data."""
        distance = activity_data.get('distance', 0)
        elevation = activity_data.get('elevation_gain', 0)
        pace = activity_data.get('average_speed', 0)
        
        # Check for scenic indicators
        location = photo_data.get('gps_data', {}).get('location_name', '')
        if any(word in location.lower() for word in ['park', 'trail', 'mountain', 'lake', 'river', 'beach']):
            return 'scenic_run'
        
        # Check for challenging run
        if elevation > 100 or (distance > 8 and pace < 5.5):  # Slow pace + distance = challenging
            return 'challenging_run'
        
        # Check for easy/recovery run
        if pace > 6.5 or distance < 5:
            return 'casual_run'
        
        # Default based on time
        time_of_day = self.analyze_time_of_day(photo_data.get('timestamp', ''))
        if time_of_day in ['morning', 'evening']:
            return f'{time_of_day}_run'
        
        return 'casual_run'
    
    def format_distance(self, distance_meters: float) -> str:
        """Format distance in a human-readable way."""
        km = distance_meters / 1000
        if km < 1:
            return f"{distance_meters:.0f}m"
        elif km.is_integer():
            return f"{km:.0f}k"
        else:
            return f"{km:.1f}k"
    
    def get_weather_description(self, photo_analysis: Dict, time_of_day: str) -> str:
        """Generate weather description from photo analysis."""
        descriptions = []
        
        if time_of_day == 'morning':
            descriptions.extend(['Perfect crisp morning', 'Beautiful start to the day', 'Morning magic'])
        elif time_of_day == 'evening':
            descriptions.extend(['Golden hour vibes', 'Perfect evening', 'Sunset therapy'])
        
        # Add more sophisticated photo analysis here when available
        return random.choice(descriptions) if descriptions else ''
    
    def get_mood_and_achievement(self, activity_data: Dict) -> tuple:
        """Determine mood and achievement level from activity data."""
        distance = activity_data.get('distance', 0) / 1000  # Convert to km
        pace = activity_data.get('average_speed', 0)  # km/h
        
        # Determine mood
        if distance > 10:
            mood = random.choice(['determination', 'grit', 'endurance'])
            achievement = 'Long run ✅'
        elif pace > 12:  # Fast pace
            mood = random.choice(['speed', 'power', 'fire'])
            achievement = 'Speed work 💨'
        else:
            mood = random.choice(['zen', 'peace', 'clarity'])
            achievement = 'Miles banked 💪'
        
        return mood, achievement
    
    def select_emojis(self, run_type: str, location: str, time_of_day: str) -> List[str]:
        """Select appropriate emojis based on context."""
        emojis = []
        
        # Running emoji
        emojis.append(random.choice(self.emoji_map['running']))
        
        # Location-based emoji
        location_lower = location.lower()
        if any(word in location_lower for word in ['mountain', 'hill']):
            emojis.append('🏔️')
        elif any(word in location_lower for word in ['park', 'forest', 'trail']):
            emojis.append(random.choice(['🌲', '🏞️']))
        elif any(word in location_lower for word in ['beach', 'lake', 'river']):
            emojis.append('🌊')
        
        # Time-based emoji
        if time_of_day == 'morning':
            emojis.append('🌅')
        elif time_of_day == 'evening':
            emojis.append('🌅')
        
        # Achievement emoji
        emojis.append(random.choice(self.emoji_map['achievement']))
        
        return emojis[:3]  # Limit to 3 emojis
    
    def generate_caption(self, activity_data: Dict, photo_data: Dict, 
                        include_sales_context: bool = False) -> str:
        """Generate a complete Strava caption."""
        
        # Extract key information
        time_of_day = self.analyze_time_of_day(photo_data.get('timestamp', ''))
        run_type = self.determine_run_type(activity_data, photo_data)
        
        distance_str = self.format_distance(activity_data.get('distance', 0))
        location = photo_data.get('gps_data', {}).get('location_name', 'the neighborhood')
        weather_desc = self.get_weather_description(photo_data.get('photo_analysis', {}), time_of_day)
        mood, achievement = self.get_mood_and_achievement(activity_data)
        
        # Add sales context if requested and appropriate
        if include_sales_context and time_of_day in ['evening', 'afternoon']:
            run_type = 'sales_context'
        
        # Select template
        templates = self.templates.get(run_type, self.templates['casual_run'])
        template = random.choice(templates)
        
        # Format the caption
        caption = template.format(
            distance=distance_str,
            location=location,
            weather_desc=weather_desc,
            mood=mood,
            achievement=achievement
        )
        
        # Add emojis
        emojis = self.select_emojis(run_type, location, time_of_day)
        caption += ' ' + ' '.join(emojis)
        
        # Add hashtags
        hashtags = self._generate_hashtags(activity_data, photo_data, run_type)
        if hashtags:
            caption += '\n\n' + ' '.join(hashtags)
        
        return caption
    
    def _generate_hashtags(self, activity_data: Dict, photo_data: Dict, run_type: str) -> List[str]:
        """Generate relevant hashtags."""
        hashtags = ['#running', '#strava']
        
        # Distance-based tags
        distance_km = activity_data.get('distance', 0) / 1000
        if distance_km > 21:
            hashtags.append('#marathon')
        elif distance_km > 10:
            hashtags.append('#longrun')
        elif distance_km > 5:
            hashtags.append('#5k')
        
        # Location-based tags
        location = photo_data.get('gps_data', {}).get('location_name', '')
        if location:
            # Extract city or notable location
            location_parts = location.split(', ')
            if location_parts:
                city_tag = '#' + re.sub(r'[^a-zA-Z0-9]', '', location_parts[0].lower())
                if len(city_tag) > 3:
                    hashtags.append(city_tag)
        
        # Time-based tags
        time_of_day = self.analyze_time_of_day(photo_data.get('timestamp', ''))
        if time_of_day == 'morning':
            hashtags.append('#morningrun')
        elif time_of_day == 'evening':
            hashtags.append('#eveningrun')
        
        # Type-based tags
        if 'scenic' in run_type:
            hashtags.append('#scenicrun')
        elif 'challenging' in run_type:
            hashtags.append('#hillrun')
        
        return hashtags[:6]  # Limit hashtags

def main():
    """Example usage of the caption generator."""
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python caption_generator.py <processed_data_json>")
        sys.exit(1)
    
    data_file = sys.argv[1]
    
    if not os.path.exists(data_file):
        print(f"Data file does not exist: {data_file}")
        sys.exit(1)
    
    with open(data_file, 'r') as f:
        processed_data = json.load(f)
    
    generator = StravaCaptionGenerator()
    
    for photo_data in processed_data:
        # Mock activity data for testing
        activity_data = {
            'distance': 5000,  # 5km in meters
            'average_speed': 10.5,  # km/h
            'elevation_gain': 50
        }
        
        caption = generator.generate_caption(activity_data, photo_data)
        
        print(f"\nPhoto: {Path(photo_data['photo_path']).name}")
        print(f"Caption:\n{caption}")
        print("-" * 50)

if __name__ == '__main__':
    main()