"""Dash callbacks for Leif's sensor data tab."""
from dash import Input, Output, dcc
from datetime import datetime
from app.leif import repository as leif_repo
from app.dashapp.leif_plots import (
    create_bs_water_temperature_plot,
    create_bs_water_level_plot,
    create_rs_temperature_plot,
    create_rs_humidity_plot,
    create_rs_pressure_plot,
    create_rs_light_spectrum_plot,
)


def register_leif_callbacks(app):
    """Register all Leif-specific Dash callbacks.

    Args:
        app: Dash application instance.
    """

    @app.callback(
        Output('leif-replica-dropdown', 'data'),
        Input('leif-date-range-picker', 'start_date'),  # triggers on initial load
    )
    def update_leif_replica_options(_):
        """Populate the replica dropdown from data present in both BS and RS tables."""
        replicas_bs = leif_repo.get_bs_replicas()
        replicas_rs = leif_repo.get_rs_replicas()
        replicas = sorted(set(replicas_bs) | set(replicas_rs))
        if not replicas:
            # Provide 1–3 as sensible defaults when no data has been ingested yet
            replicas = [1, 2, 3]
        return [{'label': f'Replica {r}', 'value': r} for r in replicas]

    @app.callback(
        [
            Output('leif-bs-water-temp-plot', 'figure'),
            Output('leif-bs-water-level-plot', 'figure'),
            Output('leif-bs-latest-table', 'data'),
            Output('leif-bs-latest-table', 'columns'),
        ],
        [
            Input('leif-date-range-picker', 'start_date'),
            Input('leif-date-range-picker', 'end_date'),
            Input('leif-replica-dropdown', 'value'),
        ],
    )
    def update_leif_bs(start_date, end_date, replicas):
        """Update all Breeding Site plots and table."""
        start_dt, end_dt = _parse_dates(start_date, end_date)
        start_str = start_dt.strftime('%Y-%m-%d %H:%M:%S')
        end_str = end_dt.strftime('%Y-%m-%d %H:%M:%S')

        df = leif_repo.fetch_bs_measurements(
            start=start_str,
            end=end_str,
            replicas=replicas if replicas else None,
        )

        temp_fig = create_bs_water_temperature_plot(df)
        level_fig = create_bs_water_level_plot(df)

        df_latest = leif_repo.fetch_latest_bs_per_replica()
        if not df_latest.empty:
            df_display = df_latest.copy()
            df_display['time_sent'] = df_display['time_sent'].dt.strftime('%Y-%m-%d %H:%M:%S')
            df_display['water_temperature'] = df_display['water_temperature'].round(3)
            df_display['distance_cm'] = df_display['distance_cm'].round(1)
            table_data = df_display.to_dict('records')
            table_cols = [{'name': col, 'id': col} for col in df_display.columns]
        else:
            table_data = []
            table_cols = []

        return temp_fig, level_fig, table_data, table_cols

    @app.callback(
        [
            Output('leif-rs-temperature-plot', 'figure'),
            Output('leif-rs-humidity-plot', 'figure'),
            Output('leif-rs-pressure-plot', 'figure'),
            Output('leif-rs-spectrum-plot', 'figure'),
            Output('leif-rs-latest-table', 'data'),
            Output('leif-rs-latest-table', 'columns'),
        ],
        [
            Input('leif-date-range-picker', 'start_date'),
            Input('leif-date-range-picker', 'end_date'),
            Input('leif-replica-dropdown', 'value'),
        ],
    )
    def update_leif_rs(start_date, end_date, replicas):
        """Update all Resting Site plots and table."""
        start_dt, end_dt = _parse_dates(start_date, end_date)
        start_str = start_dt.strftime('%Y-%m-%d %H:%M:%S')
        end_str = end_dt.strftime('%Y-%m-%d %H:%M:%S')

        df = leif_repo.fetch_rs_measurements(
            start=start_str,
            end=end_str,
            replicas=replicas if replicas else None,
        )

        temp_fig = create_rs_temperature_plot(df)
        humi_fig = create_rs_humidity_plot(df)
        pres_fig = create_rs_pressure_plot(df)
        spec_fig = create_rs_light_spectrum_plot(df)

        df_latest = leif_repo.fetch_latest_rs_per_replica()
        if not df_latest.empty:
            df_display = df_latest.copy()
            df_display['time_sent'] = df_display['time_sent'].dt.strftime('%Y-%m-%d %H:%M:%S')
            df_display['temperature'] = df_display['temperature'].round(3)
            df_display['humidity'] = df_display['humidity'].round(2)
            df_display['pressure'] = df_display['pressure'].round(2)
            table_data = df_display.to_dict('records')
            table_cols = [{'name': col, 'id': col} for col in df_display.columns]
        else:
            table_data = []
            table_cols = []

        return temp_fig, humi_fig, pres_fig, spec_fig, table_data, table_cols

    @app.callback(
        Output('leif-download-csv', 'data'),
        Input('leif-btn-download-csv-bs', 'n_clicks'),
        prevent_initial_call=True,
    )
    def download_leif_bs_data(n_clicks):
        """Trigger CSV download of all BS measurements."""
        df = leif_repo.fetch_all_bs()
        return dcc.send_data_frame(df.to_csv, filename='leif_bs_data_export.csv', index=False)

    @app.callback(
        Output('leif-download-rs-csv', 'data'),
        Input('leif-btn-download-csv-rs', 'n_clicks'),
        prevent_initial_call=True,
    )
    def download_leif_rs_data(n_clicks):
        """Trigger CSV download of all RS measurements."""
        df = leif_repo.fetch_all_rs()
        return dcc.send_data_frame(df.to_csv, filename='leif_rs_data_export.csv', index=False)


def _parse_dates(start_date, end_date):
    """Parse date strings to datetime objects covering the full days."""
    if start_date:
        start_dt = datetime.fromisoformat(start_date).replace(hour=0, minute=0, second=0)
    else:
        start_dt = datetime.now().replace(hour=0, minute=0, second=0)

    if end_date:
        end_dt = datetime.fromisoformat(end_date).replace(hour=23, minute=59, second=59)
    else:
        end_dt = datetime.now().replace(hour=23, minute=59, second=59)

    return start_dt, end_dt
