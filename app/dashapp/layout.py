"""Dash application layout."""
from dash import dcc, html, dash_table
from datetime import datetime, timedelta


def create_layout():
    """Create the Dash application layout.
    
    Returns:
        Dash layout component
    """
    # Default date range: last 24 hours
    end_date = datetime.now()
    start_date = end_date - timedelta(days=1)
    
    layout = html.Div([
        html.H1('VectorEco Dashboard', style={'textAlign': 'center', 'marginBottom': 30}),
        
        # Filters section
        html.Div([
            html.H3('Filters', style={'marginBottom': 15}),
            
            # Date range picker
            html.Div([
                html.Label('Date/Time Range:', style={'fontWeight': 'bold'}),
                dcc.DatePickerRange(
                    id='date-range-picker',
                    start_date=start_date.date(),
                    end_date=end_date.date(),
                    display_format='YYYY-MM-DD',
                    style={'marginTop': 5}
                ),
            ], style={'marginBottom': 15}),
            
            # Location filter
            html.Div([
                html.Label('Locations:', style={'fontWeight': 'bold'}),
                dcc.Dropdown(
                    id='location-dropdown',
                    options=[],
                    multi=True,
                    placeholder='Select locations (all if empty)',
                    style={'marginTop': 5}
                ),
            ], style={'marginBottom': 15}),
            
            # Container filter
            html.Div([
                html.Label('Container IDs:', style={'fontWeight': 'bold'}),
                dcc.Dropdown(
                    id='container-dropdown',
                    options=[],
                    multi=True,
                    placeholder='Select containers (all if empty)',
                    style={'marginTop': 5}
                ),
            ], style={'marginBottom': 15}),
            
            # Update button
            html.Button('Update Dashboard', id='update-button', n_clicks=0,
                       style={'width': '100%', 'padding': 10, 'fontSize': 16,
                              'backgroundColor': '#007bff', 'color': 'white',
                              'border': 'none', 'borderRadius': 5, 'cursor': 'pointer'}),
        ], style={
            'padding': 20,
            'backgroundColor': '#f8f9fa',
            'borderRadius': 10,
            'marginBottom': 30
        }),
        
        # Time series plot
        html.Div([
            html.H3('Temperature Time Series', style={'marginBottom': 15}),
            html.Img(id='timeseries-plot', style={'width': '100%'}),
        ], style={'marginBottom': 30}),
        
        # Latest status table
        html.Div([
            html.H3('Latest Status', style={'marginBottom': 15}),
            dash_table.DataTable(
                id='latest-status-table',
                columns=[],
                data=[],
                style_table={'overflowX': 'auto'},
                style_cell={
                    'textAlign': 'left',
                    'padding': '10px',
                    'fontSize': 14
                },
                style_header={
                    'backgroundColor': '#007bff',
                    'color': 'white',
                    'fontWeight': 'bold'
                },
                style_data_conditional=[
                    {
                        'if': {'row_index': 'odd'},
                        'backgroundColor': '#f8f9fa'
                    }
                ]
            ),
        ], style={'marginBottom': 30}),
        
        # Data quality view
        html.Div([
            html.H3('Data Quality - Missing Intervals', style={'marginBottom': 15}),
            html.Img(id='gap-chart', style={'width': '100%', 'marginBottom': 15}),
            dash_table.DataTable(
                id='gap-stats-table',
                columns=[],
                data=[],
                style_table={'overflowX': 'auto'},
                style_cell={
                    'textAlign': 'left',
                    'padding': '10px',
                    'fontSize': 14
                },
                style_header={
                    'backgroundColor': '#28a745',
                    'color': 'white',
                    'fontWeight': 'bold'
                },
                style_data_conditional=[
                    {
                        'if': {'row_index': 'odd'},
                        'backgroundColor': '#f8f9fa'
                    }
                ]
            ),
        ], style={'marginBottom': 30}),
        
    ], style={'maxWidth': 1400, 'margin': 'auto', 'padding': 20})
    
    return layout
