"""Database models and table creation."""
import sqlite3
from app.data.db import get_connection


DDL_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS measurements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sensor_id INTEGER NOT NULL,
    container_id INTEGER NOT NULL,
    location TEXT NOT NULL,
    timestamp DATETIME NOT NULL,
    received_at DATETIME NOT NULL,
    temperature_water REAL NOT NULL,
    temperature_air REAL NOT NULL,
    connection_quality INTEGER NOT NULL
)
"""

DDL_CREATE_UNIQUE_INDEX = """
CREATE UNIQUE INDEX IF NOT EXISTS idx_unique_measurement 
ON measurements(sensor_id, container_id, timestamp)
"""

DDL_CREATE_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_timestamp ON measurements(timestamp)",
    "CREATE INDEX IF NOT EXISTS idx_location ON measurements(location)",
    "CREATE INDEX IF NOT EXISTS idx_sensor_container ON measurements(sensor_id, container_id)",
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
