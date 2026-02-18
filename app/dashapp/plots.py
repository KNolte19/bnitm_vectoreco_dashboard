"""Seaborn plot generation and rendering for Dash."""
import io
import base64
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns


def fig_to_base64(fig) -> str:
    """Convert a matplotlib figure to base64-encoded PNG.
    
    Args:
        fig: Matplotlib figure
        
    Returns:
        Base64-encoded PNG string
    """
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight', dpi=100)
    buf.seek(0)
    img_base64 = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig)
    return img_base64


def create_timeseries_plot(df: pd.DataFrame) -> str:
    """Create a time series plot of temperatures.
    
    Args:
        df: DataFrame with timestamp, temperature_water, temperature_air columns
        
    Returns:
        Base64-encoded PNG string
    """
    if df.empty:
        # Create empty plot with message
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.text(0.5, 0.5, 'No data available for selected filters',
                ha='center', va='center', fontsize=14)
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
        return fig_to_base64(fig)
    
    # Set seaborn style
    sns.set_style("whitegrid")
    
    # Create figure
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Plot water temperature
    sns.lineplot(
        data=df,
        x='timestamp',
        y='temperature_water',
        label='Water Temperature',
        ax=ax,
        color='blue',
        linewidth=1.5
    )
    
    # Plot air temperature
    sns.lineplot(
        data=df,
        x='timestamp',
        y='temperature_air',
        label='Air Temperature',
        ax=ax,
        color='red',
        linewidth=1.5
    )
    
    ax.set_xlabel('Time', fontsize=12)
    ax.set_ylabel('Temperature (°C)', fontsize=12)
    ax.set_title('Temperature Time Series', fontsize=14, fontweight='bold')
    ax.legend(fontsize=10)
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    return fig_to_base64(fig)


def create_gap_bar_chart(df: pd.DataFrame) -> str:
    """Create a bar chart of missing measurement counts.
    
    Args:
        df: DataFrame with sensor_id, container_id, missing_count columns
        
    Returns:
        Base64-encoded PNG string
    """
    if df.empty:
        # Create empty plot with message
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.text(0.5, 0.5, 'No data available',
                ha='center', va='center', fontsize=14)
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
        return fig_to_base64(fig)
    
    # Filter to only show sensors with missing data
    df_with_gaps = df[df['missing_count'] > 0].copy()
    
    if df_with_gaps.empty:
        # No gaps found
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.text(0.5, 0.5, 'No missing measurements detected',
                ha='center', va='center', fontsize=14, color='green')
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
        return fig_to_base64(fig)
    
    # Create label for each sensor/container combination
    df_with_gaps['label'] = (
        'S' + df_with_gaps['sensor_id'].astype(str) + 
        '/C' + df_with_gaps['container_id'].astype(str)
    )
    
    # Set seaborn style
    sns.set_style("whitegrid")
    
    # Create figure
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Create bar plot
    sns.barplot(
        data=df_with_gaps,
        x='label',
        y='missing_count',
        ax=ax,
        color='coral'
    )
    
    ax.set_xlabel('Sensor/Container', fontsize=12)
    ax.set_ylabel('Missing Measurements', fontsize=12)
    ax.set_title('Missing Measurement Intervals', fontsize=14, fontweight='bold')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    
    return fig_to_base64(fig)
