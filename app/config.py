"""Configuration for the vectoreco dashboard application."""
import os
import yaml
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).parent.parent.absolute()

# Database configuration
DB_PATH = os.getenv('DB_PATH', str(BASE_DIR / 'data' / 'measurements.db'))

# Ingestion configuration
INBOX_DIR = os.getenv('INBOX_DIR', str(BASE_DIR / 'data' / 'inbox'))
ARCHIVE_DIR = os.getenv('ARCHIVE_DIR', str(BASE_DIR / 'data' / 'archive'))

# Timezone (all timestamps are UTC)
TIMEZONE = 'UTC'

# Default expected measurement frequency (used as fallback if not in sensor config)
EXPECTED_FREQ_MINUTES = 5

# Connection quality valid range
MIN_CONNECTION_QUALITY = 1
MAX_CONNECTION_QUALITY = 4

# Flask configuration
SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

# Sensor configuration file
SENSOR_CONFIG_PATH = os.getenv('SENSOR_CONFIG_PATH', str(BASE_DIR / 'sensor_config.yaml'))


def _load_sensor_config() -> dict:
    """Load the sensor configuration YAML file.

    Returns:
        Dict with sensor definitions, or empty sensors list if file not found.
    """
    try:
        with open(SENSOR_CONFIG_PATH, 'r') as f:
            data = yaml.safe_load(f) or {}
        return data
    except FileNotFoundError:
        return {'sensors': []}


SENSOR_CONFIG = _load_sensor_config()
