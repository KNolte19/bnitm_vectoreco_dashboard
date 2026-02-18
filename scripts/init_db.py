#!/usr/bin/env python3
"""Initialize the SQLite database and create tables."""
import sys
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.absolute()))

from app.data.models import create_tables
from app.data.db import get_connection
from app import config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """Initialize the database."""
    logger.info(f"Initializing database at {config.DB_PATH}")
    
    # Create parent directory if needed
    Path(config.DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    
    # Create tables and indexes
    conn = get_connection()
    try:
        create_tables(conn)
        logger.info("Database initialized successfully")
        
        # Verify table exists
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='measurements'")
        if cursor.fetchone():
            logger.info("✓ Table 'measurements' created")
        else:
            logger.error("✗ Table 'measurements' not found")
            return 1
        
        return 0
    finally:
        conn.close()


if __name__ == '__main__':
    sys.exit(main())
