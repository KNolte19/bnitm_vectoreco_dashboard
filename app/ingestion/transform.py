"""Transform parsed data into pandas DataFrame."""
import pandas as pd
from typing import List, Dict


def dicts_to_dataframe(records: List[Dict]) -> pd.DataFrame:
    """Convert a list of validated measurement dictionaries to a DataFrame.
    
    Args:
        records: List of validated measurement dictionaries
        
    Returns:
        DataFrame with proper dtypes
    """
    if not records:
        # Return empty DataFrame with correct schema
        return pd.DataFrame(columns=[
            'sensor_id', 'container_id', 'location',
            'timestamp', 'received_at',
            'temperature_water', 'temperature_air',
            'connection_quality'
        ])
    
    df = pd.DataFrame(records)
    
    # Ensure correct dtypes
    df['sensor_id'] = df['sensor_id'].astype(int)
    df['container_id'] = df['container_id'].astype(int)
    df['location'] = df['location'].astype(str)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['received_at'] = pd.to_datetime(df['received_at'])
    df['temperature_water'] = df['temperature_water'].astype(float)
    df['temperature_air'] = df['temperature_air'].astype(float)
    df['connection_quality'] = df['connection_quality'].astype(int)
    
    return df
