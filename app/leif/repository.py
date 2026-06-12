"""Repository layer for querying Leif's BS and RS sensor data."""
import pandas as pd
from typing import List, Optional
from app.leif.db import get_leif_connection


def fetch_bs_measurements(
    start: str,
    end: str,
    sites: Optional[List[int]] = None,
    replicas: Optional[List[int]] = None,
) -> pd.DataFrame:
    """Fetch Breeding Site measurements within a time range.

    Args:
        start: Start datetime (ISO format string).
        end: End datetime (ISO format string).
        sites: Optional list of site numbers to filter by.
        replicas: Optional list of replica numbers to filter by.

    Returns:
        DataFrame with columns: id, site, replica, time_sent,
        water_temperature, distance_cm.
    """
    conn = get_leif_connection()
    query = """
        SELECT id, site, replica, time_sent, water_temperature, distance_cm
        FROM leif_bs_measurements
        WHERE time_sent >= ? AND time_sent <= ?
    """
    params: list = [start, end]

    if sites:
        placeholders = ','.join('?' * len(sites))
        query += f" AND site IN ({placeholders})"
        params.extend(sites)

    if replicas:
        placeholders = ','.join('?' * len(replicas))
        query += f" AND replica IN ({placeholders})"
        params.extend(replicas)

    query += " ORDER BY time_sent ASC"

    try:
        df = pd.read_sql_query(query, conn, params=params)
        if not df.empty:
            df['time_sent'] = pd.to_datetime(df['time_sent'])
        return df
    finally:
        conn.close()


def fetch_rs_measurements(
    start: str,
    end: str,
    sites: Optional[List[int]] = None,
    replicas: Optional[List[int]] = None,
) -> pd.DataFrame:
    """Fetch Resting Site measurements within a time range.

    Args:
        start: Start datetime (ISO format string).
        end: End datetime (ISO format string).
        sites: Optional list of site numbers to filter by.
        replicas: Optional list of replica numbers to filter by.

    Returns:
        DataFrame with columns: id, site, replica, time_sent, temperature,
        humidity, pressure, full_spectrum, ir.
    """
    conn = get_leif_connection()
    query = """
        SELECT id, site, replica, time_sent,
               temperature, humidity, pressure, full_spectrum, ir
        FROM leif_rs_measurements
        WHERE time_sent >= ? AND time_sent <= ?
    """
    params: list = [start, end]

    if sites:
        placeholders = ','.join('?' * len(sites))
        query += f" AND site IN ({placeholders})"
        params.extend(sites)

    if replicas:
        placeholders = ','.join('?' * len(replicas))
        query += f" AND replica IN ({placeholders})"
        params.extend(replicas)

    query += " ORDER BY time_sent ASC"

    try:
        df = pd.read_sql_query(query, conn, params=params)
        if not df.empty:
            df['time_sent'] = pd.to_datetime(df['time_sent'])
        return df
    finally:
        conn.close()


def get_bs_replicas() -> List[int]:
    """Get all distinct replica numbers from BS measurements."""
    conn = get_leif_connection()
    try:
        df = pd.read_sql_query(
            "SELECT DISTINCT replica FROM leif_bs_measurements ORDER BY replica", conn
        )
        return df['replica'].tolist() if not df.empty else []
    finally:
        conn.close()


def get_rs_replicas() -> List[int]:
    """Get all distinct replica numbers from RS measurements."""
    conn = get_leif_connection()
    try:
        df = pd.read_sql_query(
            "SELECT DISTINCT replica FROM leif_rs_measurements ORDER BY replica", conn
        )
        return df['replica'].tolist() if not df.empty else []
    finally:
        conn.close()


def fetch_latest_bs_per_replica() -> pd.DataFrame:
    """Fetch the most recent BS measurement for each (site, replica) combination."""
    conn = get_leif_connection()
    query = """
        SELECT m.site, m.replica, m.time_sent, m.water_temperature, m.distance_cm
        FROM leif_bs_measurements m
        INNER JOIN (
            SELECT site, replica, MAX(time_sent) AS max_time
            FROM leif_bs_measurements
            GROUP BY site, replica
        ) latest
        ON m.site = latest.site
        AND m.replica = latest.replica
        AND m.time_sent = latest.max_time
        ORDER BY m.site, m.replica
    """
    try:
        df = pd.read_sql_query(query, conn)
        if not df.empty:
            df['time_sent'] = pd.to_datetime(df['time_sent'])
        return df
    finally:
        conn.close()


def fetch_latest_rs_per_replica() -> pd.DataFrame:
    """Fetch the most recent RS measurement for each (site, replica) combination."""
    conn = get_leif_connection()
    query = """
        SELECT m.site, m.replica, m.time_sent,
               m.temperature, m.humidity, m.pressure, m.full_spectrum, m.ir
        FROM leif_rs_measurements m
        INNER JOIN (
            SELECT site, replica, MAX(time_sent) AS max_time
            FROM leif_rs_measurements
            GROUP BY site, replica
        ) latest
        ON m.site = latest.site
        AND m.replica = latest.replica
        AND m.time_sent = latest.max_time
        ORDER BY m.site, m.replica
    """
    try:
        df = pd.read_sql_query(query, conn)
        if not df.empty:
            df['time_sent'] = pd.to_datetime(df['time_sent'])
        return df
    finally:
        conn.close()


def fetch_all_bs() -> pd.DataFrame:
    """Fetch all BS measurements ordered by time_sent."""
    conn = get_leif_connection()
    try:
        df = pd.read_sql_query(
            "SELECT * FROM leif_bs_measurements ORDER BY time_sent ASC", conn
        )
        if not df.empty:
            df['time_sent'] = pd.to_datetime(df['time_sent'])
        return df
    finally:
        conn.close()


def fetch_all_rs() -> pd.DataFrame:
    """Fetch all RS measurements ordered by time_sent."""
    conn = get_leif_connection()
    try:
        df = pd.read_sql_query(
            "SELECT * FROM leif_rs_measurements ORDER BY time_sent ASC", conn
        )
        if not df.empty:
            df['time_sent'] = pd.to_datetime(df['time_sent'])
        return df
    finally:
        conn.close()
