#!/usr/bin/env python3
"""Generate sample measurement data for testing the dashboard."""
import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
import random

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.absolute()))

def generate_sample_data(output_dir: str, num_days: int = 2):
    """Generate sample measurement JSON files.
    
    Args:
        output_dir: Directory to write JSON files
        num_days: Number of days of data to generate
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # 20 stations, 4 containers each
    stations = [
        ("Renke Garden 1", 1, [101, 102, 103, 104]),
        ("Lab Station 2", 2, [201, 202, 203, 204]),
        ("Field Site 3", 3, [301, 302, 303, 304]),
        ("Research Plot 4", 4, [401, 402, 403, 404]),
        ("Test Area 5", 5, [501, 502, 503, 504]),
    ]
    
    # Base timestamp - start 2 days ago
    base_time = datetime.now() - timedelta(days=num_days)
    
    # Generate measurements every 5 minutes
    intervals_per_day = 24 * 60 // 5  # 288 intervals per day
    total_intervals = intervals_per_day * num_days
    
    file_count = 0
    
    for interval in range(total_intervals):
        timestamp = base_time + timedelta(minutes=5 * interval)
        received_at = timestamp + timedelta(seconds=random.randint(1, 10))
        
        # Simulate missing data occasionally (5% chance)
        if random.random() < 0.05:
            continue
        
        for location, sensor_id, containers in stations:
            for container_id in containers:
                # Generate realistic temperature data
                # Water temp: 18-26°C with daily cycle
                hour_of_day = timestamp.hour + timestamp.minute / 60
                daily_cycle = 4 * (1 - abs((hour_of_day - 14) / 12))  # Peak at 2pm
                
                base_water_temp = 22 + daily_cycle
                water_temp = base_water_temp + random.uniform(-1, 1)
                
                # Air temp: typically 2-5°C higher than water
                air_temp = water_temp + random.uniform(2, 5)
                
                # Connection quality (most are good)
                quality_weights = [0.05, 0.1, 0.15, 0.7]  # favor quality 4
                quality = random.choices([1, 2, 3, 4], weights=quality_weights)[0]
                
                measurement = {
                    "sensor_id": sensor_id,
                    "container_id": container_id,
                    "location": location,
                    "timestamp": timestamp.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "received_at": received_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "temperature_water": round(water_temp, 1),
                    "temperature_air": round(air_temp, 1),
                    "connection_quality": quality
                }
                
                filename = f"measurement_{timestamp.strftime('%Y%m%d_%H%M%S')}_s{sensor_id}_c{container_id}.json"
                filepath = output_path / filename
                
                with open(filepath, 'w') as f:
                    json.dump(measurement, f, indent=2)
                
                file_count += 1
    
    print(f"Generated {file_count} sample measurement files in {output_dir}")
    return file_count


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate sample measurement data')
    parser.add_argument('--output', default='data/inbox', help='Output directory')
    parser.add_argument('--days', type=int, default=2, help='Number of days of data')
    
    args = parser.parse_args()
    
    generate_sample_data(args.output, args.days)
