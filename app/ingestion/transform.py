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
            'sensor_id', 'treatment_id', 'location',
            'window_start', 'window_end', 'n_observations',
            'control_temp', 'treatment_temp',
            'received_packets', 'expected_packets',
            'connection_quality',
        ])
    
    df = pd.DataFrame(records)
    
    # Ensure correct dtypes
    df['sensor_id'] = df['sensor_id'].astype(int)
    df['treatment_id'] = df['treatment_id'].astype(int)
    df['location'] = df['location'].astype(str)
    df['window_start'] = pd.to_datetime(df['window_start'])
    df['window_end'] = pd.to_datetime(df['window_end'])
    df['n_observations'] = df['n_observations'].astype(int)
    df['control_temp'] = df['control_temp'].astype(float)
    df['treatment_temp'] = df['treatment_temp'].astype(float)
    df['received_packets'] = df['received_packets'].astype(int)
    df['expected_packets'] = df['expected_packets'].astype(int)
    df['connection_quality'] = df['connection_quality'].astype(float)
    
    return df
