"""Plotly plot generation for Dash."""
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def create_timeseries_plot(df: pd.DataFrame, temp_types: list = None, separate_by_sensor_container: bool = False) -> go.Figure:
    """Create an interactive time series plot of temperatures using Plotly.
    
    Args:
        df: DataFrame with timestamp, temperature_water, temperature_air, sensor_id, container_id columns
        temp_types: List of temperature types to display ('air', 'water'). None means both.
        separate_by_sensor_container: If True, create separate lines for each sensor/container combination
        
    Returns:
        Plotly Figure object
    """
    fig = go.Figure()
    
    # Default to showing both if not specified
    if temp_types is None:
        temp_types = ['air', 'water']
    
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
    
    if separate_by_sensor_container:
        # Create separate lines for each sensor/container combination
        # Define color palettes
        water_colors = ['#3498db', '#2980b9', '#5dade2', '#1f618d', '#85c1e9', '#21618c']
        air_colors = ['#e74c3c', '#c0392b', '#ec7063', '#922b21', '#f1948a', '#641e16']
        
        # Get unique sensor/container combinations
        if 'sensor_id' in df.columns and 'container_id' in df.columns:
            combinations = df[['sensor_id', 'container_id']].drop_duplicates().sort_values(['sensor_id', 'container_id'])
            
            water_idx = 0
            air_idx = 0
            
            for _, row in combinations.iterrows():
                sensor_id = row['sensor_id']
                container_id = row['container_id']
                mask = (df['sensor_id'] == sensor_id) & (df['container_id'] == container_id)
                df_subset = df[mask].sort_values('timestamp')
                
                label_prefix = f'S{sensor_id}/C{container_id}'
                
                # Add water temperature trace if selected
                if 'water' in temp_types:
                    fig.add_trace(go.Scatter(
                        x=df_subset['timestamp'],
                        y=df_subset['temperature_water'],
                        mode='lines',
                        name=f'{label_prefix} Water',
                        line=dict(color=water_colors[water_idx % len(water_colors)], width=1.5),
                        hovertemplate=f'<b>{label_prefix} Water</b><br>Time: %{{x}}<br>Temp: %{{y:.2f}}°C<extra></extra>'
                    ))
                    water_idx += 1
                
                # Add air temperature trace if selected
                if 'air' in temp_types:
                    fig.add_trace(go.Scatter(
                        x=df_subset['timestamp'],
                        y=df_subset['temperature_air'],
                        mode='lines',
                        name=f'{label_prefix} Air',
                        line=dict(color=air_colors[air_idx % len(air_colors)], width=1.5, dash='dot'),
                        hovertemplate=f'<b>{label_prefix} Air</b><br>Time: %{{x}}<br>Temp: %{{y:.2f}}°C<extra></extra>'
                    ))
                    air_idx += 1
        else:
            # Fallback if columns are missing
            if 'water' in temp_types:
                fig.add_trace(go.Scatter(
                    x=df['timestamp'],
                    y=df['temperature_water'],
                    mode='lines',
                    name='Water Temperature',
                    line=dict(color='#3498db', width=2),
                ))
            if 'air' in temp_types:
                fig.add_trace(go.Scatter(
                    x=df['timestamp'],
                    y=df['temperature_air'],
                    mode='lines',
                    name='Air Temperature',
                    line=dict(color='#e74c3c', width=2),
                ))
    else:
        # Combined view: aggregate all data
        # Add water temperature trace if selected
        if 'water' in temp_types:
            fig.add_trace(go.Scatter(
                x=df['timestamp'],
                y=df['temperature_water'],
                mode='lines',
                name='Water Temperature',
                line=dict(color='#3498db', width=2),
                hovertemplate='<b>Water</b><br>Time: %{x}<br>Temp: %{y:.2f}°C<extra></extra>'
            ))
        
        # Add air temperature trace if selected
        if 'air' in temp_types:
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
            orientation="v",
            yanchor="top",
            y=1,
            xanchor="left",
            x=1.02
        ),
        plot_bgcolor='white',
        paper_bgcolor='white',
        height=500,
        margin=dict(l=60, r=150, t=80, b=60)
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
