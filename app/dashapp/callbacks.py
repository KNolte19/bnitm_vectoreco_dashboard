"""Dash application callbacks."""
from dash import Input, Output, State
from datetime import datetime
from app.data import repository
from app.dashapp.plots import create_timeseries_plot, create_gap_bar_chart


def register_callbacks(app):
    """Register all Dash callbacks.
    
    Args:
        app: Dash application instance
    """
    
    @app.callback(
        [
            Output('location-dropdown', 'options'),
            Output('container-dropdown', 'options'),
        ],
        Input('update-button', 'n_clicks')
    )
    def update_filter_options(n_clicks):
        """Update available options for location and container dropdowns."""
        locations = repository.get_all_locations()
        containers = repository.get_all_container_ids()
        
        location_options = [{'label': loc, 'value': loc} for loc in locations]
        container_options = [{'label': str(c), 'value': c} for c in containers]
        
        return location_options, container_options
    
    @app.callback(
        [
            Output('timeseries-plot', 'src'),
            Output('latest-status-table', 'data'),
            Output('latest-status-table', 'columns'),
            Output('gap-chart', 'src'),
            Output('gap-stats-table', 'data'),
            Output('gap-stats-table', 'columns'),
        ],
        Input('update-button', 'n_clicks'),
        [
            State('date-range-picker', 'start_date'),
            State('date-range-picker', 'end_date'),
            State('location-dropdown', 'value'),
            State('container-dropdown', 'value'),
            State('quality-slider', 'value'),
        ]
    )
    def update_dashboard(n_clicks, start_date, end_date, locations, containers, min_quality):
        """Update all dashboard components based on filters."""
        # Parse dates and add time component (full day range)
        if start_date:
            start_dt = datetime.fromisoformat(start_date).replace(hour=0, minute=0, second=0)
        else:
            start_dt = datetime.now().replace(hour=0, minute=0, second=0)
        
        if end_date:
            end_dt = datetime.fromisoformat(end_date).replace(hour=23, minute=59, second=59)
        else:
            end_dt = datetime.now().replace(hour=23, minute=59, second=59)
        
        start_str = start_dt.strftime('%Y-%m-%d %H:%M:%S')
        end_str = end_dt.strftime('%Y-%m-%d %H:%M:%S')
        
        # Fetch measurements for time series
        df_measurements = repository.fetch_measurements(
            start=start_str,
            end=end_str,
            locations=locations if locations else None,
            container_ids=containers if containers else None,
            min_quality=min_quality if min_quality > 1 else None
        )
        
        # Create time series plot
        timeseries_img = create_timeseries_plot(df_measurements)
        timeseries_src = f"data:image/png;base64,{timeseries_img}"
        
        # Fetch latest status
        df_latest = repository.fetch_latest_per_location_container()
        
        # Format latest status for table
        if not df_latest.empty:
            df_latest_display = df_latest.copy()
            df_latest_display['timestamp'] = df_latest_display['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
            df_latest_display['received_at'] = df_latest_display['received_at'].dt.strftime('%Y-%m-%d %H:%M:%S')
            
            # Round temperatures
            df_latest_display['temperature_water'] = df_latest_display['temperature_water'].round(2)
            df_latest_display['temperature_air'] = df_latest_display['temperature_air'].round(2)
            
            latest_data = df_latest_display.to_dict('records')
            latest_columns = [{'name': col, 'id': col} for col in df_latest_display.columns]
        else:
            latest_data = []
            latest_columns = []
        
        # Fetch gap statistics
        df_gaps = repository.fetch_gap_stats(
            start=start_str,
            end=end_str,
            expected_freq='5min'
        )
        
        # Create gap bar chart
        gap_img = create_gap_bar_chart(df_gaps)
        gap_src = f"data:image/png;base64,{gap_img}"
        
        # Format gap stats for table
        if not df_gaps.empty:
            gap_data = df_gaps.to_dict('records')
            gap_columns = [{'name': col, 'id': col} for col in df_gaps.columns]
        else:
            gap_data = []
            gap_columns = []
        
        return (
            timeseries_src,
            latest_data,
            latest_columns,
            gap_src,
            gap_data,
            gap_columns
        )
