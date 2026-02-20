"""Plotly plot generation for Dash."""
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from app.ingestion.parser import TREATMENT_LABELS, TREATMENT_DELTA_RANGES

# Colours per treatment
TREATMENT_COLORS = {
    1: '#e67e22',   # orange  (+1.5°C)
    2: '#e74c3c',   # red     (+3°C)
    3: '#8e44ad',   # purple  (+4.5°C)
}
CONTROL_COLOR = '#3498db'  # blue


def _quality_to_color(quality: float, max_quality: float = 1.0) -> str:
    """Map a connection quality value (0–1) to an RGB color string.

    0 → red, 1 → green, intermediate values are interpolated.

    Args:
        quality: Connection quality value (0.0–1.0).
        max_quality: Maximum quality value (default 1.0).

    Returns:
        CSS-compatible color string, e.g. 'rgb(255,0,0)'.
    """
    if pd.isna(quality):
        return 'rgb(128,128,128)'
    ratio = max(0.0, min(1.0, quality / max_quality))
    r = int(255 * (1.0 - ratio))
    g = int(255 * ratio)
    return f'rgb({r},{g},0)'


def create_timeseries_plot(
    df: pd.DataFrame,
    treatment_ids: list = None,
    temp_mode: str = 'absolute',
) -> go.Figure:
    """Create an interactive time series plot of temperatures.

    Args:
        df: DataFrame with window_start, control_temp, treatment_temp,
            sensor_id, treatment_id columns.
        treatment_ids: List of treatment IDs to display. None means all.
        temp_mode: 'absolute' to show raw temperatures, 'delta' to show
                   (treatment_temp - control_temp) per treatment.

    Returns:
        Plotly Figure object
    """
    fig = go.Figure()

    if df.empty:
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

    available_treatments = sorted(df['treatment_id'].unique())
    if treatment_ids:
        available_treatments = [t for t in available_treatments if t in treatment_ids]

    if temp_mode == 'delta':
        # Plot temperature delta (treatment - control) per treatment
        for tid in available_treatments:
            subset = df[df['treatment_id'] == tid].sort_values('window_start').copy()
            subset['delta'] = subset['treatment_temp'] - subset['control_temp']
            label = TREATMENT_LABELS.get(tid, f"Treatment {tid}")
            color = TREATMENT_COLORS.get(tid, '#95a5a6')

            fig.add_trace(go.Scatter(
                x=subset['window_start'],
                y=subset['delta'],
                mode='lines',
                name=f'{label}',
                line=dict(color=color, width=2),
                hovertemplate=(
                    f'<b>{label}</b><br>'
                    'Time: %{x}<br>'
                    'ΔT: %{y:.2f}°C<extra></extra>'
                )
            ))

        # Add target range shading for each treatment
        for tid in available_treatments:
            if tid in TREATMENT_DELTA_RANGES:
                lo, hi = TREATMENT_DELTA_RANGES[tid]
                color = TREATMENT_COLORS.get(tid, '#95a5a6')
                label = TREATMENT_LABELS.get(tid, f"Treatment {tid}")
                # Upper bound (invisible line)
                fig.add_trace(go.Scatter(
                    x=[df['window_start'].min(), df['window_start'].max()],
                    y=[hi, hi],
                    mode='lines',
                    line=dict(color=color, width=1, dash='dot'),
                    showlegend=False,
                    hoverinfo='skip',
                ))
                # Lower bound with fill
                fig.add_trace(go.Scatter(
                    x=[df['window_start'].min(), df['window_start'].max()],
                    y=[lo, lo],
                    mode='lines',
                    fill='tonexty',
                    fillcolor=color.replace(')', ', 0.1)').replace('rgb', 'rgba'),
                    line=dict(color=color, width=1, dash='dot'),
                    name=f'{label} target range',
                    hoverinfo='skip',
                ))

        y_title = 'Temperature Difference (°C)'
        title_text = 'Treatment Temperature Difference from Control'

    else:
        # Absolute mode: show control temp + treatment temps
        # Control temperature – use treatment 1's control as representative
        # (all treatments share the same control window, so we de-duplicate by window)
        df_control = (
            df.sort_values('window_start')
              .drop_duplicates(subset=['sensor_id', 'window_start'])
        )
        if not df_control.empty:
            fig.add_trace(go.Scatter(
                x=df_control['window_start'],
                y=df_control['control_temp'],
                mode='lines',
                name='Control',
                line=dict(color=CONTROL_COLOR, width=2),
                hovertemplate='<b>Control</b><br>Time: %{x}<br>Temp: %{y:.2f}°C<extra></extra>'
            ))

        # Treatment temperatures
        for tid in available_treatments:
            subset = df[df['treatment_id'] == tid].sort_values('window_start')
            label = TREATMENT_LABELS.get(tid, f"Treatment {tid}")
            color = TREATMENT_COLORS.get(tid, '#95a5a6')

            fig.add_trace(go.Scatter(
                x=subset['window_start'],
                y=subset['treatment_temp'],
                mode='lines',
                name=label,
                line=dict(color=color, width=2),
                hovertemplate=(
                    f'<b>{label}</b><br>'
                    'Time: %{x}<br>'
                    'Temp: %{y:.2f}°C<extra></extra>'
                )
            ))

        y_title = 'Temperature (°C)'
        title_text = 'Absolute Temperature by Treatment'

    fig.update_layout(
        title=dict(
            text=title_text,
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
            title=y_title,
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
        df: DataFrame with sensor_id, treatment_id, missing_count columns
        
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
    
    # Create label for each sensor/treatment combination
    df_with_gaps['label'] = (
        'S' + df_with_gaps['sensor_id'].astype(str) +
        '/T' + df_with_gaps['treatment_id'].astype(str)
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
            text='Missing Measurement Intervals by Sensor/Treatment',
            font=dict(size=18, color='#2c3e50'),
            x=0.5,
            xanchor='center'
        ),
        xaxis=dict(
            title='Sensor/Treatment',
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
               red (quality = 0) to green (quality = 1)

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
                f"Avg quality: {row.avg_quality:.2f}"
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
            cmin=0, cmax=1,
            color=[0],
            colorbar=dict(
                title='Avg<br>Quality',
                thickness=15,
                len=0.7,
                tickvals=[0, 0.25, 0.5, 0.75, 1.0],
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
