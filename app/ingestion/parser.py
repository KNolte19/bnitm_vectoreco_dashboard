"""JSON file parser and validator."""
import json
import logging
from typing import Dict, Optional, Tuple
from datetime import datetime, timezone
from dateutil import parser as dateutil_parser
from app import config

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Raised when JSON validation fails."""
    pass


def parse_json_file(filepath: str) -> Tuple[Optional[Dict], Optional[str]]:
    """Parse and validate a JSON measurement file.
    
    Args:
        filepath: Path to JSON file
        
    Returns:
        Tuple of (parsed_dict, error_message)
        - If successful: (dict, None)
        - If failed: (None, error_message)
    """
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        # Validate required fields
        required_fields = [
            'sensor_id', 'container_id', 'location',
            'timestamp', 'received_at',
            'temperature_water', 'temperature_air',
            'connection_quality'
        ]
        
        for field in required_fields:
            if field not in data:
                return None, f"Missing required field: {field}"
        
        # Validate and normalize data
        validated = {}
        
        # Integer fields
        try:
            validated['sensor_id'] = int(data['sensor_id'])
            validated['container_id'] = int(data['container_id'])
        except (ValueError, TypeError) as e:
            return None, f"Invalid integer field: {e}"
        
        # Location (string)
        validated['location'] = str(data['location'])
        
        # Datetime fields (must be timezone-aware UTC)
        try:
            timestamp = dateutil_parser.parse(data['timestamp'])
            if timestamp.tzinfo is None:
                # Assume UTC if no timezone
                timestamp = timestamp.replace(tzinfo=timezone.utc)
            # Convert to UTC and format as ISO string
            validated['timestamp'] = timestamp.astimezone(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
            
            received_at = dateutil_parser.parse(data['received_at'])
            if received_at.tzinfo is None:
                received_at = received_at.replace(tzinfo=timezone.utc)
            validated['received_at'] = received_at.astimezone(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
        except (ValueError, TypeError) as e:
            return None, f"Invalid datetime field: {e}"
        
        # Temperature fields (float)
        try:
            validated['temperature_water'] = float(data['temperature_water'])
            validated['temperature_air'] = float(data['temperature_air'])
        except (ValueError, TypeError) as e:
            return None, f"Invalid temperature field: {e}"
        
        # Connection quality (integer, range 1-4)
        try:
            quality = int(data['connection_quality'])
            if quality < config.MIN_CONNECTION_QUALITY or quality > config.MAX_CONNECTION_QUALITY:
                return None, f"Connection quality {quality} out of valid range (1-4)"
            validated['connection_quality'] = quality
        except (ValueError, TypeError) as e:
            return None, f"Invalid connection_quality field: {e}"
        
        return validated, None
        
    except json.JSONDecodeError as e:
        return None, f"JSON parse error: {e}"
    except Exception as e:
        return None, f"Unexpected error: {e}"
