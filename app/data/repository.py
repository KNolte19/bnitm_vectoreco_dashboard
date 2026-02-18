"""Repository layer for querying measurements data."""
import pandas as pd
from typing import Optional, List
from app.data.db import get_connection
from app import config


def fetch_measurements(
    start: str,
    end: str,
    locations: Optional[List[str]] = None,
    sensor_ids: Optional[List[int]] = None,
    container_ids: Optional[List[int]] = None,
    min_quality: Optional[int] = None
) -> pd.DataFrame:
    """Fetch measurements within a time range with optional filters.
    
    Args:
        start: Start datetime (ISO format string)
        end: End datetime (ISO format string)
        locations: Optional list of locations to filter by
        sensor_ids: Optional list of sensor IDs to filter by
        container_ids: Optional list of container IDs to filter by
        min_quality: Optional minimum connection quality (1-4)
        
    Returns:
        DataFrame with measurement records
    """
    conn = get_connection()
    
    query = """
        SELECT 
            id, sensor_id, container_id, location,
            timestamp, received_at,
            temperature_water, temperature_air,
            connection_quality
        FROM measurements
        WHERE timestamp >= ? AND timestamp <= ?
    """
    params = [start, end]
    
    if locations:
        placeholders = ','.join('?' * len(locations))
        query += f" AND location IN ({placeholders})"
        params.extend(locations)
    
    if sensor_ids:
        placeholders = ','.join('?' * len(sensor_ids))
        query += f" AND sensor_id IN ({placeholders})"
        params.extend(sensor_ids)
    
    if container_ids:
        placeholders = ','.join('?' * len(container_ids))
        query += f" AND container_id IN ({placeholders})"
        params.extend(container_ids)
    
    if min_quality is not None:
        query += " AND connection_quality >= ?"
        params.append(min_quality)
    
    query += " ORDER BY timestamp ASC"
    
    try:
        df = pd.read_sql_query(query, conn, params=params)
        # Parse datetime columns
        if not df.empty:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df['received_at'] = pd.to_datetime(df['received_at'])
        return df
    finally:
        conn.close()


def fetch_latest_per_location_container() -> pd.DataFrame:
    """Fetch the most recent measurement for each (location, container_id) combination.
    
    Returns:
        DataFrame with latest measurements per location/container
    """
    conn = get_connection()
    
    query = """
        SELECT 
            m.location,
            m.container_id,
            m.sensor_id,
            m.timestamp,
            m.received_at,
            m.temperature_water,
            m.temperature_air,
            m.connection_quality
        FROM measurements m
        INNER JOIN (
            SELECT location, container_id, MAX(timestamp) as max_timestamp
            FROM measurements
            GROUP BY location, container_id
        ) latest
        ON m.location = latest.location 
        AND m.container_id = latest.container_id
        AND m.timestamp = latest.max_timestamp
        ORDER BY m.location, m.container_id
    """
    
    try:
        df = pd.read_sql_query(query, conn)
        if not df.empty:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df['received_at'] = pd.to_datetime(df['received_at'])
        return df
    finally:
        conn.close()


def fetch_gap_stats(
    start: str,
    end: str,
    expected_freq: str = "5min"
) -> pd.DataFrame:
    """Calculate missing measurement intervals for each (sensor_id, container_id).
    
    Args:
        start: Start datetime (ISO format string)
        end: End datetime (ISO format string)
        expected_freq: Expected frequency as pandas freq string (default: "5min")
        
    Returns:
        DataFrame with gap statistics per sensor/container
    """
    conn = get_connection()
    
    query = """
        SELECT 
            sensor_id,
            container_id,
            location,
            timestamp
        FROM measurements
        WHERE timestamp >= ? AND timestamp <= ?
        ORDER BY sensor_id, container_id, timestamp
    """
    
    try:
        df = pd.read_sql_query(query, conn, params=[start, end])
        
        if df.empty:
            return pd.DataFrame(columns=[
                'sensor_id', 'container_id', 'location',
                'expected_count', 'actual_count', 'missing_count'
            ])
        
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Calculate expected number of measurements using pd.Timedelta
        start_dt = pd.to_datetime(start)
        end_dt = pd.to_datetime(end)
        freq_delta = pd.Timedelta(expected_freq)
        total_duration = end_dt - start_dt
        expected_count = int(total_duration / freq_delta) + 1
        
        # Group by sensor_id and container_id to count actual measurements
        stats = df.groupby(['sensor_id', 'container_id', 'location']).agg(
            actual_count=('timestamp', 'count')
        ).reset_index()
        
        stats['expected_count'] = expected_count
        stats['missing_count'] = stats['expected_count'] - stats['actual_count']
        stats['missing_count'] = stats['missing_count'].clip(lower=0)
        
        return stats
    finally:
        conn.close()


def get_all_locations() -> List[str]:
    """Get all unique locations from the database.
    
    Returns:
        List of location names
    """
    conn = get_connection()
    
    query = "SELECT DISTINCT location FROM measurements ORDER BY location"
    
    try:
        df = pd.read_sql_query(query, conn)
        return df['location'].tolist() if not df.empty else []
    finally:
        conn.close()


def get_all_sensor_ids() -> List[int]:
    """Get all unique sensor IDs from the database.
    
    Returns:
        List of sensor IDs
    """
    conn = get_connection()
    
    query = "SELECT DISTINCT sensor_id FROM measurements ORDER BY sensor_id"
    
    try:
        df = pd.read_sql_query(query, conn)
        return df['sensor_id'].tolist() if not df.empty else []
    finally:
        conn.close()


def get_all_container_ids() -> List[int]:
    """Get all unique container IDs from the database.
    
    Returns:
        List of container IDs
    """
    conn = get_connection()
    
    query = "SELECT DISTINCT container_id FROM measurements ORDER BY container_id"
    
    try:
        df = pd.read_sql_query(query, conn)
        return df['container_id'].tolist() if not df.empty else []
    finally:
        conn.close()


def get_sensors_by_location(locations: Optional[List[str]] = None) -> List[int]:
    """Get sensor IDs filtered by location(s).
    
    Args:
        locations: Optional list of locations to filter by
        
    Returns:
        List of sensor IDs available for the given locations
    """
    conn = get_connection()
    
    if locations:
        placeholders = ','.join('?' * len(locations))
        query = f"SELECT DISTINCT sensor_id FROM measurements WHERE location IN ({placeholders}) ORDER BY sensor_id"
        params = locations
    else:
        query = "SELECT DISTINCT sensor_id FROM measurements ORDER BY sensor_id"
        params = []
    
    try:
        df = pd.read_sql_query(query, conn, params=params)
        return df['sensor_id'].tolist() if not df.empty else []
    finally:
        conn.close()


def get_containers_by_location_and_sensor(
    locations: Optional[List[str]] = None,
    sensor_ids: Optional[List[int]] = None
) -> List[int]:
    """Get container IDs filtered by location(s) and/or sensor(s).
    
    Args:
        locations: Optional list of locations to filter by
        sensor_ids: Optional list of sensor IDs to filter by
        
    Returns:
        List of container IDs available for the given filters
    """
    conn = get_connection()
    
    query = "SELECT DISTINCT container_id FROM measurements WHERE 1=1"
    params = []
    
    if locations:
        placeholders = ','.join('?' * len(locations))
        query += f" AND location IN ({placeholders})"
        params.extend(locations)
    
    if sensor_ids:
        placeholders = ','.join('?' * len(sensor_ids))
        query += f" AND sensor_id IN ({placeholders})"
        params.extend(sensor_ids)
    
    query += " ORDER BY container_id"
    
    try:
        df = pd.read_sql_query(query, conn, params=params)
        return df['container_id'].tolist() if not df.empty else []
    finally:
        conn.close()
