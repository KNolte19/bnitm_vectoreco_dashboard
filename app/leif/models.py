"""Database models and table creation for Leif's sensor data."""
import sqlite3
from app.leif.db import get_leif_connection

# ── Breeding Site (BS) table ──────────────────────────────────────────────────
DDL_BS_TABLE = """
CREATE TABLE IF NOT EXISTS leif_bs_measurements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    site INTEGER NOT NULL,
    replica INTEGER NOT NULL,
    time_sent DATETIME NOT NULL,
    water_temperature REAL NOT NULL,
    distance_cm REAL NOT NULL
)
"""

DDL_BS_UNIQUE_INDEX = """
CREATE UNIQUE INDEX IF NOT EXISTS idx_unique_bs
ON leif_bs_measurements(site, replica, time_sent)
"""

DDL_BS_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_bs_time_sent ON leif_bs_measurements(time_sent)",
    "CREATE INDEX IF NOT EXISTS idx_bs_site_replica ON leif_bs_measurements(site, replica)",
]

# ── Resting Site (RS) table ───────────────────────────────────────────────────
DDL_RS_TABLE = """
CREATE TABLE IF NOT EXISTS leif_rs_measurements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    site INTEGER NOT NULL,
    replica INTEGER NOT NULL,
    time_sent DATETIME NOT NULL,
    temperature REAL NOT NULL,
    humidity REAL NOT NULL,
    pressure REAL NOT NULL,
    full_spectrum INTEGER NOT NULL,
    ir INTEGER NOT NULL
)
"""

DDL_RS_UNIQUE_INDEX = """
CREATE UNIQUE INDEX IF NOT EXISTS idx_unique_rs
ON leif_rs_measurements(site, replica, time_sent)
"""

DDL_RS_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_rs_time_sent ON leif_rs_measurements(time_sent)",
    "CREATE INDEX IF NOT EXISTS idx_rs_site_replica ON leif_rs_measurements(site, replica)",
]


def create_leif_tables(conn: sqlite3.Connection = None):
    """Create BS and RS tables plus indexes in Leif's database.

    Args:
        conn: Optional database connection. If None, creates a new one.
    """
    close_conn = False
    if conn is None:
        conn = get_leif_connection()
        close_conn = True

    try:
        cursor = conn.cursor()

        # Breeding Site table
        cursor.execute(DDL_BS_TABLE)
        cursor.execute(DDL_BS_UNIQUE_INDEX)
        for idx_sql in DDL_BS_INDEXES:
            cursor.execute(idx_sql)

        # Resting Site table
        cursor.execute(DDL_RS_TABLE)
        cursor.execute(DDL_RS_UNIQUE_INDEX)
        for idx_sql in DDL_RS_INDEXES:
            cursor.execute(idx_sql)

        conn.commit()
    finally:
        if close_conn:
            conn.close()
