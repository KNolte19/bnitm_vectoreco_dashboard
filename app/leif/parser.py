"""JSONL file parser for Leif's BS and RS sensor data."""
import json
import logging
from typing import Dict, List, Optional, Tuple
from datetime import timezone
from dateutil import parser as dateutil_parser

logger = logging.getLogger(__name__)

# Required fields per logger type
_BS_FIELDS = ['water_temperature', 'distance_cm']
_RS_FIELDS = ['temperature', 'humidity', 'pressure', 'full_spectrum', 'ir']
_COMMON_FIELDS = ['time_sent', 'site', 'logger', 'replica']


class ValidationError(Exception):
    """Raised when JSONL validation fails."""
    pass


def _parse_time_sent(value: str) -> str:
    """Parse and normalise a time_sent value to a UTC string.

    Args:
        value: Raw timestamp string from JSON.

    Returns:
        UTC datetime string in '%Y-%m-%d %H:%M:%S' format.
    """
    dt = dateutil_parser.parse(str(value))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')


def parse_jsonl_file(
    filepath: str,
) -> Tuple[Optional[List[Tuple[str, Dict]]], Optional[str]]:
    """Parse a JSONL file containing Leif's BS or RS sensor records.

    Each non-empty line must be a valid JSON object with a ``logger`` field
    set to ``"BS"`` (Breeding Site) or ``"RS"`` (Resting Site).

    Args:
        filepath: Path to the ``.jsonl`` file.

    Returns:
        Tuple of (results, error_message) where:
        - On success: (list of ``(logger_type, record_dict)`` tuples, None)
        - On failure: (None, error_description)
    """
    try:
        results: List[Tuple[str, Dict]] = []

        with open(filepath, 'r') as f:
            for line_num, raw_line in enumerate(f, 1):
                line = raw_line.strip()
                if not line:
                    continue

                try:
                    data = json.loads(line)
                except json.JSONDecodeError as exc:
                    return None, f"JSON parse error on line {line_num}: {exc}"

                # Validate common fields
                for field in _COMMON_FIELDS:
                    if field not in data:
                        return None, f"Missing required field '{field}' on line {line_num}"

                logger_type = data['logger']
                if logger_type not in ('BS', 'RS'):
                    return None, (
                        f"Unknown logger type '{logger_type}' on line {line_num}; "
                        "expected 'BS' or 'RS'"
                    )

                try:
                    time_sent = _parse_time_sent(data['time_sent'])
                except (ValueError, TypeError) as exc:
                    return None, f"Invalid time_sent on line {line_num}: {exc}"

                try:
                    site = int(data['site'])
                    replica = int(data['replica'])
                except (ValueError, TypeError) as exc:
                    return None, f"Invalid site/replica on line {line_num}: {exc}"

                if logger_type == 'BS':
                    for field in _BS_FIELDS:
                        if field not in data:
                            return None, (
                                f"BS record missing required field '{field}' on line {line_num}"
                            )
                    try:
                        record: Dict = {
                            'site': site,
                            'replica': replica,
                            'time_sent': time_sent,
                            'water_temperature': float(data['water_temperature']),
                            'distance_cm': float(data['distance_cm']),
                        }
                    except (ValueError, TypeError) as exc:
                        return None, f"Invalid BS field value on line {line_num}: {exc}"

                else:  # RS
                    for field in _RS_FIELDS:
                        if field not in data:
                            return None, (
                                f"RS record missing required field '{field}' on line {line_num}"
                            )
                    try:
                        record = {
                            'site': site,
                            'replica': replica,
                            'time_sent': time_sent,
                            'temperature': float(data['temperature']),
                            'humidity': float(data['humidity']),
                            'pressure': float(data['pressure']),
                            'full_spectrum': int(data['full_spectrum']),
                            'ir': int(data['ir']),
                        }
                    except (ValueError, TypeError) as exc:
                        return None, f"Invalid RS field value on line {line_num}: {exc}"

                results.append((logger_type, record))

        if not results:
            return None, "JSONL file contains no valid records"

        return results, None

    except FileNotFoundError:
        return None, f"File not found: {filepath}"
    except Exception as exc:
        return None, f"Unexpected error: {exc}"
