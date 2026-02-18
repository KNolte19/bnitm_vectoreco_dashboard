"""Database connection and engine helper."""
import sqlite3
from pathlib import Path
from typing import Optional
from app import config


def get_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    """Get a SQLite database connection.
    
    Args:
        db_path: Path to the database file. If None, uses config.DB_PATH.
        
    Returns:
        sqlite3.Connection: Database connection.
    """
    if db_path is None:
        db_path = config.DB_PATH
    
    # Ensure parent directory exists
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    # Enable foreign keys
    conn.execute("PRAGMA foreign_keys = ON")
    return conn
