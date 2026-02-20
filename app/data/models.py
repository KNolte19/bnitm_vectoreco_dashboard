"""Database models and table creation."""
import sqlite3
from app.data.db import get_connection


DDL_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS measurements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sensor_id INTEGER NOT NULL,
    treatment_id INTEGER NOT NULL,
    location TEXT NOT NULL,
    window_start DATETIME NOT NULL,
    window_end DATETIME NOT NULL,
    n_observations INTEGER NOT NULL,
    control_temp REAL NOT NULL,
    treatment_temp REAL NOT NULL,
    received_packets INTEGER NOT NULL,
    expected_packets INTEGER NOT NULL,
    connection_quality REAL NOT NULL
)
"""

DDL_CREATE_UNIQUE_INDEX = """
CREATE UNIQUE INDEX IF NOT EXISTS idx_unique_measurement 
ON measurements(sensor_id, treatment_id, window_start)
"""

DDL_CREATE_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_window_start ON measurements(window_start)",
    "CREATE INDEX IF NOT EXISTS idx_location ON measurements(location)",
    "CREATE INDEX IF NOT EXISTS idx_sensor_treatment ON measurements(sensor_id, treatment_id)",
]


def create_tables(conn: sqlite3.Connection = None):
    """Create the database schema with tables and indexes.
    
    Args:
        conn: Optional database connection. If None, creates a new one.
    """
    close_conn = False
    if conn is None:
        conn = get_connection()
        close_conn = True
    
    try:
        cursor = conn.cursor()
        
        # Create table
        cursor.execute(DDL_CREATE_TABLE)
        
        # Create unique index for deduplication
        cursor.execute(DDL_CREATE_UNIQUE_INDEX)
        
        # Create additional indexes for query performance
        for index_sql in DDL_CREATE_INDEXES:
            cursor.execute(index_sql)
        
        conn.commit()
    finally:
        if close_conn:
            conn.close()
