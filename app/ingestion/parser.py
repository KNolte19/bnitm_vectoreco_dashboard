"""JSON file parser and validator."""
import json
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timezone
from dateutil import parser as dateutil_parser
from app import config

logger = logging.getLogger(__name__)

# Treatment expected delta ranges (min, max) in °C above control
TREATMENT_DELTA_RANGES = {
    1: (1.3, 1.7),
    2: (2.8, 3.2),
    3: (4.3, 4.7),
}

TREATMENT_LABELS = {
    1: "+1.5°C",
    2: "+3°C",
    3: "+4.5°C",
}


class ValidationError(Exception):
    """Raised when JSON validation fails."""
    pass


def _lookup_location(sensor_id: int) -> str:
    """Look up the location string for a sensor_id from config."""
    for sensor in config.SENSOR_CONFIG.get('sensors', []):
        if sensor.get('id') == sensor_id:
            return sensor.get('location', 'Unknown')
    return 'Unknown'


def parse_json_file(filepath: str) -> Tuple[Optional[List[Dict]], Optional[str]]:
    """Parse and validate a JSON measurement file in the new format.

    Each file contains one time window for one site with multiple treatments.

    Args:
        filepath: Path to JSON file

    Returns:
        Tuple of (list_of_records, error_message)
        - If successful: (list, None)  – one dict per treatment
        - If failed: (None, error_message)
    """
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)

        # Validate top-level required fields
        top_required = ['site_id', 'window_start', 'window_end', 'n_observations', 'treatments']
        for field in top_required:
            if field not in data:
                return None, f"Missing required field: {field}"

        # Validate and parse top-level fields
        try:
            sensor_id = int(data['site_id'])
        except (ValueError, TypeError) as e:
            return None, f"Invalid site_id: {e}"

        try:
            n_observations = int(data['n_observations'])
        except (ValueError, TypeError) as e:
            return None, f"Invalid n_observations: {e}"

        try:
            window_start = dateutil_parser.parse(data['window_start'])
            if window_start.tzinfo is None:
                window_start = window_start.replace(tzinfo=timezone.utc)
            window_start_str = window_start.astimezone(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')

            window_end = dateutil_parser.parse(data['window_end'])
            if window_end.tzinfo is None:
                window_end = window_end.replace(tzinfo=timezone.utc)
            window_end_str = window_end.astimezone(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
        except (ValueError, TypeError) as e:
            return None, f"Invalid datetime field: {e}"

        location = _lookup_location(sensor_id)

        treatments = data['treatments']
        if not isinstance(treatments, list) or len(treatments) == 0:
            return None, "treatments must be a non-empty list"

        records = []
        for t in treatments:
            # Validate treatment required fields
            t_required = [
                'treatment_id', 'mean_control_temp', 'mean_treatment_temp',
                'received_packets', 'expected_packets', 'connection_quality',
            ]
            for field in t_required:
                if field not in t:
                    return None, f"Treatment missing required field: {field}"

            try:
                treatment_id = int(t['treatment_id'])
            except (ValueError, TypeError) as e:
                return None, f"Invalid treatment_id: {e}"

            try:
                control_temp = float(t['mean_control_temp'])
                treatment_temp = float(t['mean_treatment_temp'])
            except (ValueError, TypeError) as e:
                return None, f"Invalid temperature field: {e}"

            try:
                received_packets = int(t['received_packets'])
                expected_packets = int(t['expected_packets'])
            except (ValueError, TypeError) as e:
                return None, f"Invalid packets field: {e}"

            try:
                quality = float(t['connection_quality'])
                if quality < config.MIN_CONNECTION_QUALITY or quality > config.MAX_CONNECTION_QUALITY:
                    return None, f"Connection quality {quality} out of valid range (0.0-1.0)"
            except (ValueError, TypeError) as e:
                return None, f"Invalid connection_quality field: {e}"

            records.append({
                'sensor_id': sensor_id,
                'treatment_id': treatment_id,
                'location': location,
                'window_start': window_start_str,
                'window_end': window_end_str,
                'n_observations': n_observations,
                'control_temp': control_temp,
                'treatment_temp': treatment_temp,
                'received_packets': received_packets,
                'expected_packets': expected_packets,
                'connection_quality': quality,
            })

        return records, None

    except json.JSONDecodeError as e:
        return None, f"JSON parse error: {e}"
    except Exception as e:
        return None, f"Unexpected error: {e}"
