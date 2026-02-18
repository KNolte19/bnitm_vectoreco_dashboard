"""Configuration for the vectoreco dashboard application."""
import os
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

# Expected measurement frequency
EXPECTED_FREQ_MINUTES = 5

# Connection quality valid range
MIN_CONNECTION_QUALITY = 1
MAX_CONNECTION_QUALITY = 4

# Flask configuration
SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
