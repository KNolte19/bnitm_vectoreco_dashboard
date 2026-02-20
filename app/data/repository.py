"""Repository layer for querying measurements data."""
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, List
from app.data.db import get_connection
from app import config


def fetch_measurements(
    start: str,
    end: str,
    locations: Optional[List[str]] = None,
    sensor_ids: Optional[List[int]] = None,
    treatment_ids: Optional[List[int]] = None,
    min_quality: Optional[float] = None
) -> pd.DataFrame:
    """Fetch measurements within a time range with optional filters.
    
    Args:
        start: Start datetime (ISO format string)
        end: End datetime (ISO format string)
        locations: Optional list of locations to filter by
        sensor_ids: Optional list of sensor IDs to filter by
        treatment_ids: Optional list of treatment IDs to filter by
        min_quality: Optional minimum connection quality (0.0-1.0)
        
    Returns:
        DataFrame with measurement records
    """
    conn = get_connection()
    
    query = """
        SELECT 
            id, sensor_id, treatment_id, location,
            window_start, window_end, n_observations,
            control_temp, treatment_temp,
            received_packets, expected_packets,
            connection_quality
        FROM measurements
        WHERE window_start >= ? AND window_start <= ?
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
    
    if treatment_ids:
        placeholders = ','.join('?' * len(treatment_ids))
        query += f" AND treatment_id IN ({placeholders})"
        params.extend(treatment_ids)
    
    if min_quality is not None:
        query += " AND connection_quality >= ?"
        params.append(min_quality)
    
    query += " ORDER BY window_start ASC"
    
    try:
        df = pd.read_sql_query(query, conn, params=params)
        # Parse datetime columns
        if not df.empty:
            df['window_start'] = pd.to_datetime(df['window_start'])
            df['window_end'] = pd.to_datetime(df['window_end'])
        return df
    finally:
        conn.close()


def fetch_latest_per_location_treatment() -> pd.DataFrame:
    """Fetch the most recent measurement for each (location, treatment_id) combination.
    
    Returns:
        DataFrame with latest measurements per location/treatment
    """
    conn = get_connection()
    
    query = """
        SELECT 
            m.location,
            m.treatment_id,
            m.sensor_id,
            m.window_start,
            m.window_end,
            m.control_temp,
            m.treatment_temp,
            m.received_packets,
            m.expected_packets,
            m.connection_quality
        FROM measurements m
        INNER JOIN (
            SELECT location, treatment_id, MAX(window_start) as max_window_start
            FROM measurements
            GROUP BY location, treatment_id
        ) latest
        ON m.location = latest.location 
        AND m.treatment_id = latest.treatment_id
        AND m.window_start = latest.max_window_start
        ORDER BY m.location, m.treatment_id
    """
    
    try:
        df = pd.read_sql_query(query, conn)
        if not df.empty:
            df['window_start'] = pd.to_datetime(df['window_start'])
            df['window_end'] = pd.to_datetime(df['window_end'])
        return df
    finally:
        conn.close()


def fetch_gap_stats(
    start: str,
    end: str,
    expected_freq: str = "15min"
) -> pd.DataFrame:
    """Calculate missing measurement intervals for each (sensor_id, treatment_id).
    
    Args:
        start: Start datetime (ISO format string)
        end: End datetime (ISO format string)
        expected_freq: Expected frequency as pandas freq string (default: "15min")
        
    Returns:
        DataFrame with gap statistics per sensor/treatment
    """
    conn = get_connection()
    
    query = """
        SELECT 
            sensor_id,
            treatment_id,
            location,
            window_start
        FROM measurements
        WHERE window_start >= ? AND window_start <= ?
        ORDER BY sensor_id, treatment_id, window_start
    """
    
    try:
        df = pd.read_sql_query(query, conn, params=[start, end])
        
        if df.empty:
            return pd.DataFrame(columns=[
                'sensor_id', 'treatment_id', 'location',
                'expected_count', 'actual_count', 'missing_count'
            ])
        
        df['window_start'] = pd.to_datetime(df['window_start'])
        
        # Calculate expected number of measurements using pd.Timedelta
        start_dt = pd.to_datetime(start)
        end_dt = pd.to_datetime(end)
        freq_delta = pd.Timedelta(expected_freq)
        total_duration = end_dt - start_dt
        expected_count = int(total_duration / freq_delta) + 1
        
        # Group by sensor_id and treatment_id to count actual measurements
        stats = df.groupby(['sensor_id', 'treatment_id', 'location']).agg(
            actual_count=('window_start', 'count')
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


def get_all_treatment_ids() -> List[int]:
    """Get all unique treatment IDs from the database.
    
    Returns:
        List of treatment IDs
    """
    conn = get_connection()
    
    query = "SELECT DISTINCT treatment_id FROM measurements ORDER BY treatment_id"
    
    try:
        df = pd.read_sql_query(query, conn)
        return df['treatment_id'].tolist() if not df.empty else []
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


def get_treatments_by_location_and_sensor(
    locations: Optional[List[str]] = None,
    sensor_ids: Optional[List[int]] = None
) -> List[int]:
    """Get treatment IDs filtered by location(s) and/or sensor(s).
    
    Args:
        locations: Optional list of locations to filter by
        sensor_ids: Optional list of sensor IDs to filter by
        
    Returns:
        List of treatment IDs available for the given filters
    """
    conn = get_connection()
    
    query = "SELECT DISTINCT treatment_id FROM measurements WHERE 1=1"
    params = []
    
    if locations:
        placeholders = ','.join('?' * len(locations))
        query += f" AND location IN ({placeholders})"
        params.extend(locations)
    
    if sensor_ids:
        placeholders = ','.join('?' * len(sensor_ids))
        query += f" AND sensor_id IN ({placeholders})"
        params.extend(sensor_ids)
    
    query += " ORDER BY treatment_id"
    
    try:
        df = pd.read_sql_query(query, conn, params=params)
        return df['treatment_id'].tolist() if not df.empty else []
    finally:
        conn.close()


def fetch_connectivity_stats(
    start: str,
    end: str,
    locations: Optional[List[str]] = None,
    sensor_ids: Optional[List[int]] = None,
) -> pd.DataFrame:
    """Fetch connectivity statistics grouped by adaptive time bins.

    For each (time_bin, sensor_id) the function computes:
    - received_count : total received packets
    - expected_count : total expected packets
    - avg_quality    : mean connection_quality value
    - ratio          : received_count / expected_count (capped at 1.0)

    Args:
        start: Start datetime (ISO format string)
        end: End datetime (ISO format string)
        locations: Optional list of locations to filter by
        sensor_ids: Optional list of sensor IDs to filter by

    Returns:
        DataFrame with columns: time_bin, sensor_id, location,
        received_count, expected_count, avg_quality, ratio
    """
    conn = get_connection()

    query = """
        SELECT sensor_id, location, window_start,
               received_packets, expected_packets, connection_quality
        FROM measurements
        WHERE window_start >= ? AND window_start <= ?
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

    query += " ORDER BY sensor_id, window_start"

    try:
        df = pd.read_sql_query(query, conn, params=params)

        empty_cols = [
            'time_bin', 'sensor_id', 'location',
            'received_count', 'expected_count', 'avg_quality', 'ratio',
        ]
        if df.empty:
            return pd.DataFrame(columns=empty_cols)

        df['window_start'] = pd.to_datetime(df['window_start'])

        # Choose adaptive bin size based on the selected time range
        start_dt = pd.to_datetime(start)
        end_dt = pd.to_datetime(end)
        duration = end_dt - start_dt

        if duration <= pd.Timedelta('3 days'):
            bin_freq = '1h'
        elif duration <= pd.Timedelta('30 days'):
            bin_freq = '6h'
        else:
            bin_freq = '1D'

        df['time_bin'] = df['window_start'].dt.floor(bin_freq)

        stats = df.groupby(['time_bin', 'sensor_id', 'location']).agg(
            received_count=('received_packets', 'sum'),
            expected_count=('expected_packets', 'sum'),
            avg_quality=('connection_quality', 'mean'),
        ).reset_index()

        stats['ratio'] = (
            stats['received_count'] / stats['expected_count'].clip(lower=1)
        ).clip(upper=1.0)

        return stats
    finally:
        conn.close()


def check_sensor_gaps(gap_threshold_hours: float = 3.0) -> List[dict]:
    """Check for sensors that had a signal gap >= threshold in the last 24 h.

    Also reports sensors defined in the config that sent no messages at all
    during the last 24 hours.

    Args:
        gap_threshold_hours: Minimum gap duration (hours) that triggers a warning.

    Returns:
        List of dicts with keys sensor_id, location, max_gap_hours for each
        sensor that exceeded the threshold.
    """
    now = datetime.utcnow()
    window_start = now - timedelta(hours=24)

    start_str = window_start.strftime('%Y-%m-%d %H:%M:%S')
    end_str = now.strftime('%Y-%m-%d %H:%M:%S')

    conn = get_connection()
    query = """
        SELECT sensor_id, location, window_start
        FROM measurements
        WHERE window_start >= ? AND window_start <= ?
        ORDER BY sensor_id, location, window_start
    """

    try:
        df = pd.read_sql_query(query, conn, params=[start_str, end_str])

        if not df.empty:
            df['window_start'] = pd.to_datetime(df['window_start'])

        issues = []
        seen_sensors = set()

        if not df.empty:
            for (sensor_id, location), group in df.groupby(['sensor_id', 'location']):
                seen_sensors.add(sensor_id)
                timestamps = group['window_start'].sort_values().tolist()

                # Include the window boundaries for gap calculation
                all_points = (
                    [pd.Timestamp(window_start)] + timestamps + [pd.Timestamp(now)]
                )

                max_gap = max(
                    (all_points[i + 1] - all_points[i]).total_seconds() / 3600
                    for i in range(len(all_points) - 1)
                )

                if max_gap >= gap_threshold_hours:
                    issues.append({
                        'sensor_id': sensor_id,
                        'location': location,
                        'max_gap_hours': round(max_gap, 1),
                    })

        # Sensors in config that sent nothing in the last 24 h
        for sensor in config.SENSOR_CONFIG.get('sensors', []):
            sid = sensor['id']
            if sid not in seen_sensors:
                issues.append({
                    'sensor_id': sid,
                    'location': sensor.get('location', 'unknown'),
                    'max_gap_hours': 24.0,
                })

        return issues
    finally:
        conn.close()
