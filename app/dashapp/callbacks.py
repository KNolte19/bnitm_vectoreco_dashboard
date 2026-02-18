"""Dash application callbacks."""
from dash import Input, Output
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
            Output('sensor-dropdown', 'options'),
            Output('container-dropdown', 'options'),
        ],
        [
            Input('date-range-picker', 'start_date'),  # Triggers on initial load
            Input('location-dropdown', 'value'),
            Input('sensor-dropdown', 'value'),
        ]
    )
    def update_filter_options(_, selected_locations, selected_sensors):
        """Update available options for sensor and container dropdowns based on location selection."""
        # Always show all locations
        locations = repository.get_all_locations()
        location_options = [{'label': loc, 'value': loc} for loc in locations]
        
        # Filter sensors based on selected locations
        if selected_locations:
            available_sensors = repository.get_sensors_by_location(selected_locations)
        else:
            available_sensors = repository.get_all_sensor_ids()
        sensor_options = [{'label': f'Sensor {s}', 'value': s} for s in available_sensors]
        
        # Filter containers based on selected locations and sensors
        if selected_locations or selected_sensors:
            available_containers = repository.get_containers_by_location_and_sensor(
                selected_locations, selected_sensors
            )
        else:
            available_containers = repository.get_all_container_ids()
        container_options = [{'label': f'Container {c}', 'value': c} for c in available_containers]
        
        return location_options, sensor_options, container_options
    
    @app.callback(
        [
            Output('timeseries-plot', 'figure'),
            Output('latest-status-table', 'data'),
            Output('latest-status-table', 'columns'),
            Output('gap-chart', 'figure'),
            Output('gap-stats-table', 'data'),
            Output('gap-stats-table', 'columns'),
        ],
        [
            Input('date-range-picker', 'start_date'),
            Input('date-range-picker', 'end_date'),
            Input('location-dropdown', 'value'),
            Input('sensor-dropdown', 'value'),
            Input('container-dropdown', 'value'),
            Input('temperature-type-checklist', 'value'),
            Input('separate-lines-checklist', 'value'),
        ]
    )
    def update_dashboard(start_date, end_date, locations, sensors, containers, temp_types, separate_lines):
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
            sensor_ids=sensors if sensors else None,
            container_ids=containers if containers else None,
        )
        
        # Create time series plot
        separate = 'separate' in separate_lines if separate_lines else False
        timeseries_fig = create_timeseries_plot(df_measurements, temp_types, separate)
        
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
        gap_fig = create_gap_bar_chart(df_gaps)
        
        # Format gap stats for table
        if not df_gaps.empty:
            gap_data = df_gaps.to_dict('records')
            gap_columns = [{'name': col, 'id': col} for col in df_gaps.columns]
        else:
            gap_data = []
            gap_columns = []
        
        return (
            timeseries_fig,
            latest_data,
            latest_columns,
            gap_fig,
            gap_data,
            gap_columns
        )
