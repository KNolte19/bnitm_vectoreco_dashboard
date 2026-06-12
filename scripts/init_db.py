#!/usr/bin/env python3
"""Initialize the SQLite databases and create tables."""
import sys
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.absolute()))

from app.data.models import create_tables
from app.data.db import get_connection
from app.leif.models import create_leif_tables
from app.leif.db import get_leif_connection
from app import config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def _init_felix_db() -> int:
    """Initialise Felix's measurements database.

    Returns:
        0 on success, 1 on failure.
    """
    logger.info("Initialising Felix's database at %s", config.DB_PATH)
    Path(config.DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = get_connection()
    try:
        create_tables(conn)
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


def _init_leif_db() -> int:
    """Initialise Leif's sensor database.

    Returns:
        0 on success, 1 on failure.
    """
    logger.info("Initialising Leif's database at %s", config.LEIF_DB_PATH)
    Path(config.LEIF_DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = get_leif_connection()
    try:
        create_leif_tables(conn)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='leif_bs_measurements'"
        )
        if cursor.fetchone():
            logger.info("✓ Table 'leif_bs_measurements' created")
        else:
            logger.error("✗ Table 'leif_bs_measurements' not found")
            return 1
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='leif_rs_measurements'"
        )
        if cursor.fetchone():
            logger.info("✓ Table 'leif_rs_measurements' created")
        else:
            logger.error("✗ Table 'leif_rs_measurements' not found")
            return 1
        return 0
    finally:
        conn.close()


def main():
    """Initialize both databases."""
    rc = _init_felix_db()
    if rc != 0:
        return rc
    rc = _init_leif_db()
    if rc != 0:
        return rc
    logger.info("All databases initialised successfully")
    return 0


if __name__ == '__main__':
    sys.exit(main())
