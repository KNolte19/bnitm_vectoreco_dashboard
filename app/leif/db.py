"""Database connection for Leif's separate sensor database."""
import sqlite3
from pathlib import Path
from typing import Optional
from app import config


def get_leif_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    """Get a SQLite connection to Leif's database.

    Args:
        db_path: Path to the database file. If None, uses config.LEIF_DB_PATH.

    Returns:
        sqlite3.Connection: Database connection.
    """
    if db_path is None:
        db_path = config.LEIF_DB_PATH

    Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn
