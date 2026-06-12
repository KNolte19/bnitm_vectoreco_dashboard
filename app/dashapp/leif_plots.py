"""Plotly plot generation for Leif's BS and RS sensor data."""
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Colour palette per replica
REPLICA_COLORS = {
    1: '#2196F3',   # blue
    2: '#FF9800',   # orange
    3: '#4CAF50',   # green
}
_DEFAULT_COLOR = '#9C27B0'  # purple for any unexpected replica


def _replica_color(replica: int) -> str:
    return REPLICA_COLORS.get(replica, _DEFAULT_COLOR)


def _empty_fig(message: str = "No data available for selected filters") -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(
        text=message,
        xref="paper", yref="paper",
        x=0.5, y=0.5, showarrow=False,
        font=dict(size=16, color="gray"),
    )
    fig.update_layout(
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        height=350,
        plot_bgcolor='white',
        paper_bgcolor='white',
    )
    return fig


def _base_layout(title: str, y_title: str, height: int = 380) -> dict:
    return dict(
        title=dict(text=title, font=dict(size=16, color='#2c3e50'), x=0.5, xanchor='center'),
        xaxis=dict(title='Time', showgrid=True, gridcolor='#ecf0f1', zeroline=False),
        yaxis=dict(title=y_title, showgrid=True, gridcolor='#ecf0f1', zeroline=False),
        hovermode='x unified',
        legend=dict(orientation='v', yanchor='top', y=1, xanchor='left', x=1.02),
        plot_bgcolor='white',
        paper_bgcolor='white',
        height=height,
        margin=dict(l=60, r=130, t=60, b=60),
    )


# ── Breeding Site (BS) plots ─────────────────────────────────────────────────

def create_bs_water_temperature_plot(df: pd.DataFrame) -> go.Figure:
    """Line chart of water temperature over time, one line per replica.

    Args:
        df: DataFrame with columns time_sent, replica, water_temperature.

    Returns:
        Plotly Figure.
    """
    if df.empty:
        return _empty_fig()

    fig = go.Figure()
    for replica in sorted(df['replica'].unique()):
        subset = df[df['replica'] == replica].sort_values('time_sent')
        color = _replica_color(replica)
        fig.add_trace(go.Scatter(
            x=subset['time_sent'],
            y=subset['water_temperature'],
            mode='lines+markers',
            name=f'Replica {replica}',
            line=dict(color=color, width=2),
            marker=dict(size=4),
            hovertemplate=(
                f'<b>Replica {replica}</b><br>'
                'Time: %{x}<br>'
                'Water temp: %{y:.2f} °C<extra></extra>'
            ),
        ))

    fig.update_layout(**_base_layout('Breeding Site – Water Temperature', 'Water Temperature (°C)'))
    return fig


def create_bs_water_level_plot(df: pd.DataFrame) -> go.Figure:
    """Line chart of water level (distance_cm) over time, one line per replica.

    Higher distance_cm values indicate a lower water level (sensor-to-surface
    distance increases as the water drops).

    Args:
        df: DataFrame with columns time_sent, replica, distance_cm.

    Returns:
        Plotly Figure.
    """
    if df.empty:
        return _empty_fig()

    fig = go.Figure()
    for replica in sorted(df['replica'].unique()):
        subset = df[df['replica'] == replica].sort_values('time_sent')
        color = _replica_color(replica)
        fig.add_trace(go.Scatter(
            x=subset['time_sent'],
            y=subset['distance_cm'],
            mode='lines+markers',
            name=f'Replica {replica}',
            line=dict(color=color, width=2),
            marker=dict(size=4),
            hovertemplate=(
                f'<b>Replica {replica}</b><br>'
                'Time: %{x}<br>'
                'Distance: %{y:.1f} cm<extra></extra>'
            ),
        ))

    fig.update_layout(**_base_layout(
        'Breeding Site – Distance to Water Surface', 'Distance (cm)'
    ))
    return fig


# ── Resting Site (RS) plots ──────────────────────────────────────────────────

def create_rs_temperature_plot(df: pd.DataFrame) -> go.Figure:
    """Line chart of air temperature at resting sites, one line per replica.

    Args:
        df: DataFrame with columns time_sent, replica, temperature.

    Returns:
        Plotly Figure.
    """
    if df.empty:
        return _empty_fig()

    fig = go.Figure()
    for replica in sorted(df['replica'].unique()):
        subset = df[df['replica'] == replica].sort_values('time_sent')
        color = _replica_color(replica)
        fig.add_trace(go.Scatter(
            x=subset['time_sent'],
            y=subset['temperature'],
            mode='lines+markers',
            name=f'Replica {replica}',
            line=dict(color=color, width=2),
            marker=dict(size=4),
            hovertemplate=(
                f'<b>Replica {replica}</b><br>'
                'Time: %{x}<br>'
                'Temperature: %{y:.2f} °C<extra></extra>'
            ),
        ))

    fig.update_layout(**_base_layout('Resting Site – Air Temperature', 'Temperature (°C)'))
    return fig


def create_rs_humidity_plot(df: pd.DataFrame) -> go.Figure:
    """Line chart of relative humidity at resting sites, one line per replica.

    Args:
        df: DataFrame with columns time_sent, replica, humidity.

    Returns:
        Plotly Figure.
    """
    if df.empty:
        return _empty_fig()

    fig = go.Figure()
    for replica in sorted(df['replica'].unique()):
        subset = df[df['replica'] == replica].sort_values('time_sent')
        color = _replica_color(replica)
        fig.add_trace(go.Scatter(
            x=subset['time_sent'],
            y=subset['humidity'],
            mode='lines+markers',
            name=f'Replica {replica}',
            line=dict(color=color, width=2),
            marker=dict(size=4),
            hovertemplate=(
                f'<b>Replica {replica}</b><br>'
                'Time: %{x}<br>'
                'Humidity: %{y:.1f} %<extra></extra>'
            ),
        ))

    fig.update_layout(**_base_layout('Resting Site – Relative Humidity', 'Humidity (%)'))
    return fig


def create_rs_pressure_plot(df: pd.DataFrame) -> go.Figure:
    """Line chart of air pressure at resting sites, one line per replica.

    Args:
        df: DataFrame with columns time_sent, replica, pressure.

    Returns:
        Plotly Figure.
    """
    if df.empty:
        return _empty_fig()

    fig = go.Figure()
    for replica in sorted(df['replica'].unique()):
        subset = df[df['replica'] == replica].sort_values('time_sent')
        color = _replica_color(replica)
        fig.add_trace(go.Scatter(
            x=subset['time_sent'],
            y=subset['pressure'],
            mode='lines+markers',
            name=f'Replica {replica}',
            line=dict(color=color, width=2),
            marker=dict(size=4),
            hovertemplate=(
                f'<b>Replica {replica}</b><br>'
                'Time: %{x}<br>'
                'Pressure: %{y:.1f} hPa<extra></extra>'
            ),
        ))

    fig.update_layout(**_base_layout('Resting Site – Air Pressure', 'Pressure (hPa)'))
    return fig


def create_rs_light_spectrum_plot(df: pd.DataFrame) -> go.Figure:
    """Line chart of full spectrum and IR light values at resting sites.

    One line per (replica × sensor_type) pair using solid lines for full
    spectrum and dashed lines for IR.

    Args:
        df: DataFrame with columns time_sent, replica, full_spectrum, ir.

    Returns:
        Plotly Figure.
    """
    if df.empty:
        return _empty_fig()

    fig = go.Figure()
    for replica in sorted(df['replica'].unique()):
        subset = df[df['replica'] == replica].sort_values('time_sent')
        color = _replica_color(replica)

        fig.add_trace(go.Scatter(
            x=subset['time_sent'],
            y=subset['full_spectrum'],
            mode='lines+markers',
            name=f'Full Spectrum – Replica {replica}',
            line=dict(color=color, width=2, dash='solid'),
            marker=dict(size=4),
            hovertemplate=(
                f'<b>Full Spectrum – Replica {replica}</b><br>'
                'Time: %{x}<br>'
                'Value: %{y}<extra></extra>'
            ),
        ))
        fig.add_trace(go.Scatter(
            x=subset['time_sent'],
            y=subset['ir'],
            mode='lines+markers',
            name=f'IR – Replica {replica}',
            line=dict(color=color, width=2, dash='dash'),
            marker=dict(size=4, symbol='diamond'),
            hovertemplate=(
                f'<b>IR – Replica {replica}</b><br>'
                'Time: %{x}<br>'
                'Value: %{y}<extra></extra>'
            ),
        ))

    fig.update_layout(**_base_layout('Resting Site – Light Spectrum', 'Raw Count'))
    return fig
