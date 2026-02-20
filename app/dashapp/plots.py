"""Plotly plot generation for Dash."""
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def _quality_to_color(quality: float, max_quality: float = 4.0) -> str:
    """Map a connection quality value (0–4) to an RGB color string.

    0 → red, max_quality → green, intermediate values are interpolated.

    Args:
        quality: Connection quality value.
        max_quality: Maximum quality value (default 4).

    Returns:
        CSS-compatible color string, e.g. 'rgb(255,0,0)'.
    """
    if pd.isna(quality):
        return 'rgb(128,128,128)'
    ratio = max(0.0, min(1.0, quality / max_quality))
    r = int(255 * (1.0 - ratio))
    g = int(255 * ratio)
    return f'rgb({r},{g},0)'


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


def create_connectivity_bar_chart(df: pd.DataFrame) -> go.Figure:
    """Create a bar chart showing network connectivity over time.

    Each bar represents one time bin for one sensor and shows:
    - Height : ratio of received packets to expected packets (0–1)
    - Color  : average connection quality for that bin, mapped from
               red (quality = 0) to green (quality = 4)

    Args:
        df: DataFrame returned by repository.fetch_connectivity_stats with
            columns time_bin, sensor_id, location, received_count,
            expected_count, avg_quality, ratio.

    Returns:
        Plotly Figure object.
    """
    fig = go.Figure()

    if df.empty:
        fig.add_annotation(
            text="No data available for selected filters",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16, color="gray"),
        )
        fig.update_layout(
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            height=400,
        )
        return fig

    # One trace per sensor so bars can be grouped by time bin
    sensor_ids = sorted(df['sensor_id'].unique())

    for sensor_id in sensor_ids:
        subset = df[df['sensor_id'] == sensor_id].sort_values('time_bin')
        location = subset['location'].iloc[0] if not subset.empty else ''

        colors = [_quality_to_color(q) for q in subset['avg_quality']]

        hover_text = [
            (
                f"<b>Sensor {sensor_id} – {location}</b><br>"
                f"Time: {row.time_bin}<br>"
                f"Received: {row.received_count} / {row.expected_count} expected<br>"
                f"Ratio: {row.ratio:.0%}<br>"
                f"Avg quality: {row.avg_quality:.1f}"
            )
            for row in subset.itertuples()
        ]

        fig.add_trace(go.Bar(
            name=f"Sensor {sensor_id} ({location})",
            x=subset['time_bin'],
            y=subset['ratio'],
            marker=dict(color=colors, line=dict(width=0.5, color='rgba(0,0,0,0.2)')),
            hovertemplate='%{customdata}<extra></extra>',
            customdata=hover_text,
        ))

    # Add a dummy invisible scatter trace to act as a quality colorbar
    fig.add_trace(go.Scatter(
        x=[None], y=[None],
        mode='markers',
        marker=dict(
            colorscale=[[0, 'rgb(255,0,0)'], [1, 'rgb(0,255,0)']],
            cmin=0, cmax=4,
            color=[0],
            colorbar=dict(
                title='Avg<br>Quality',
                thickness=15,
                len=0.7,
                tickvals=[0, 1, 2, 3, 4],
            ),
            showscale=True,
        ),
        showlegend=False,
        hoverinfo='skip',
    ))

    fig.update_layout(
        title=dict(
            text='Network Connectivity – Received / Expected Packets',
            font=dict(size=18, color='#2c3e50'),
            x=0.5,
            xanchor='center',
        ),
        barmode='group',
        xaxis=dict(
            title='Time',
            showgrid=True,
            gridcolor='#ecf0f1',
        ),
        yaxis=dict(
            title='Received / Expected',
            range=[0, 1.05],
            tickformat='.0%',
            showgrid=True,
            gridcolor='#ecf0f1',
            zeroline=False,
        ),
        legend=dict(orientation='v', yanchor='top', y=1, xanchor='left', x=1.08),
        plot_bgcolor='white',
        paper_bgcolor='white',
        height=450,
        margin=dict(l=60, r=150, t=80, b=80),
    )

    return fig
