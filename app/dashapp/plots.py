"""Plotly plot generation for Dash."""
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def create_timeseries_plot(df: pd.DataFrame) -> go.Figure:
    """Create an interactive time series plot of temperatures using Plotly.
    
    Args:
        df: DataFrame with timestamp, temperature_water, temperature_air columns
        
    Returns:
        Plotly Figure object
    """
    fig = go.Figure()
    
    if df.empty:
        # Create empty plot with message
        fig.add_annotation(
            text="No data available for selected filters",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16, color="gray")
        )
        fig.update_layout(
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            height=400
        )
        return fig
    
    # Add water temperature trace
    fig.add_trace(go.Scatter(
        x=df['timestamp'],
        y=df['temperature_water'],
        mode='lines',
        name='Water Temperature',
        line=dict(color='#3498db', width=2),
        hovertemplate='<b>Water</b><br>Time: %{x}<br>Temp: %{y:.2f}°C<extra></extra>'
    ))
    
    # Add air temperature trace
    fig.add_trace(go.Scatter(
        x=df['timestamp'],
        y=df['temperature_air'],
        mode='lines',
        name='Air Temperature',
        line=dict(color='#e74c3c', width=2),
        hovertemplate='<b>Air</b><br>Time: %{x}<br>Temp: %{y:.2f}°C<extra></extra>'
    ))
    
    # Update layout
    fig.update_layout(
        title=dict(
            text='Temperature Time Series',
            font=dict(size=18, color='#2c3e50'),
            x=0.5,
            xanchor='center'
        ),
        xaxis=dict(
            title='Time',
            showgrid=True,
            gridcolor='#ecf0f1',
            zeroline=False
        ),
        yaxis=dict(
            title='Temperature (°C)',
            showgrid=True,
            gridcolor='#ecf0f1',
            zeroline=False
        ),
        hovermode='x unified',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        plot_bgcolor='white',
        paper_bgcolor='white',
        height=500,
        margin=dict(l=60, r=30, t=80, b=60)
    )
    
    return fig


def create_gap_bar_chart(df: pd.DataFrame) -> go.Figure:
    """Create an interactive bar chart of missing measurement counts using Plotly.
    
    Args:
        df: DataFrame with sensor_id, container_id, missing_count columns
        
    Returns:
        Plotly Figure object
    """
    fig = go.Figure()
    
    if df.empty:
        # Create empty plot with message
        fig.add_annotation(
            text="No data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16, color="gray")
        )
        fig.update_layout(
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            height=400
        )
        return fig
    
    # Filter to only show sensors with missing data
    df_with_gaps = df[df['missing_count'] > 0].copy()
    
    if df_with_gaps.empty:
        # No gaps found
        fig.add_annotation(
            text="✓ No missing measurements detected",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=18, color="#27ae60")
        )
        fig.update_layout(
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            height=400
        )
        return fig
    
    # Create label for each sensor/container combination
    df_with_gaps['label'] = (
        'S' + df_with_gaps['sensor_id'].astype(str) + 
        '/C' + df_with_gaps['container_id'].astype(str)
    )
    
    # Create bar chart
    fig.add_trace(go.Bar(
        x=df_with_gaps['label'],
        y=df_with_gaps['missing_count'],
        marker=dict(
            color='#e67e22',
            line=dict(color='#d35400', width=1)
        ),
        hovertemplate='<b>%{x}</b><br>Missing: %{y}<extra></extra>'
    ))
    
    # Update layout
    fig.update_layout(
        title=dict(
            text='Missing Measurement Intervals by Sensor/Container',
            font=dict(size=18, color='#2c3e50'),
            x=0.5,
            xanchor='center'
        ),
        xaxis=dict(
            title='Sensor/Container',
            showgrid=False,
            tickangle=-45
        ),
        yaxis=dict(
            title='Missing Measurements',
            showgrid=True,
            gridcolor='#ecf0f1',
            zeroline=False
        ),
        plot_bgcolor='white',
        paper_bgcolor='white',
        height=400,
        margin=dict(l=60, r=30, t=80, b=100),
        showlegend=False
    )
    
    return fig
