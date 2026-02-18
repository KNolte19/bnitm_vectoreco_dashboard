"""Dash application layout."""
from dash import dcc, html, dash_table
from datetime import datetime, timedelta

# Constants
TABLE_PAGE_SIZE = 10


def create_layout():
    """Create the Dash application layout.
    
    Returns:
        Dash layout component
    """
    # Default date range: last 24 hours
    end_date = datetime.now()
    start_date = end_date - timedelta(days=1)
    
    layout = html.Div([
        html.H1('VectorEco Dashboard', 
                style={'textAlign': 'center', 'marginBottom': 30, 'color': '#2c3e50'}),
        
        # Filters section
        html.Div([
            html.H3('Filters', style={'marginBottom': 15, 'color': '#34495e'}),
            
            html.Div([
                # Date range picker
                html.Div([
                    html.Label('Date/Time Range:', style={'fontWeight': 'bold', 'display': 'block', 'marginBottom': 5}),
                    dcc.DatePickerRange(
                        id='date-range-picker',
                        start_date=start_date.date(),
                        end_date=end_date.date(),
                        display_format='YYYY-MM-DD',
                        style={'width': '100%'}
                    ),
                ], style={'marginBottom': 15}),
                
                # Location filter
                html.Div([
                    html.Label('Locations:', style={'fontWeight': 'bold', 'display': 'block', 'marginBottom': 5}),
                    dcc.Dropdown(
                        id='location-dropdown',
                        options=[],
                        multi=True,
                        placeholder='Select locations (all if empty)',
                    ),
                ], style={'marginBottom': 15}),
                
                # Sensor filter
                html.Div([
                    html.Label('Sensor IDs:', style={'fontWeight': 'bold', 'display': 'block', 'marginBottom': 5}),
                    dcc.Dropdown(
                        id='sensor-dropdown',
                        options=[],
                        multi=True,
                        placeholder='Select sensors (all if empty)',
                    ),
                ], style={'marginBottom': 15}),
                
                # Container filter
                html.Div([
                    html.Label('Container IDs:', style={'fontWeight': 'bold', 'display': 'block', 'marginBottom': 5}),
                    dcc.Dropdown(
                        id='container-dropdown',
                        options=[],
                        multi=True,
                        placeholder='Select containers (all if empty)',
                    ),
                ], style={'marginBottom': 15}),
            ]),
            
        ], style={
            'padding': 20,
            'backgroundColor': '#ecf0f1',
            'borderRadius': 8,
            'marginBottom': 30,
            'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'
        }),
        
        # Time series plot
        html.Div([
            html.H3('Temperature Over Time', 
                   style={'marginBottom': 15, 'color': '#34495e'}),
            dcc.Graph(id='timeseries-plot', 
                     config={'displayModeBar': True, 'displaylogo': False}),
        ], style={
            'marginBottom': 30,
            'padding': 20,
            'backgroundColor': 'white',
            'borderRadius': 8,
            'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'
        }),
        
        # Latest status table
        html.Div([
            html.H3('Latest Status', 
                   style={'marginBottom': 15, 'color': '#34495e'}),
            dash_table.DataTable(
                id='latest-status-table',
                columns=[],
                data=[],
                style_table={'overflowX': 'auto'},
                style_cell={
                    'textAlign': 'left',
                    'padding': '12px',
                    'fontSize': 13,
                    'fontFamily': 'Arial, sans-serif'
                },
                style_header={
                    'backgroundColor': '#3498db',
                    'color': 'white',
                    'fontWeight': 'bold',
                    'border': '1px solid #2980b9'
                },
                style_data_conditional=[
                    {
                        'if': {'row_index': 'odd'},
                        'backgroundColor': '#f8f9fa'
                    }
                ],
                page_size=TABLE_PAGE_SIZE,
            ),
        ], style={
            'marginBottom': 30,
            'padding': 20,
            'backgroundColor': 'white',
            'borderRadius': 8,
            'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'
        }),
        
        # Data quality view
        html.Div([
            html.H3('Data Quality - Missing Intervals', 
                   style={'marginBottom': 15, 'color': '#34495e'}),
            dcc.Graph(id='gap-chart',
                     config={'displayModeBar': True, 'displaylogo': False}),
            dash_table.DataTable(
                id='gap-stats-table',
                columns=[],
                data=[],
                style_table={'overflowX': 'auto', 'marginTop': 20},
                style_cell={
                    'textAlign': 'left',
                    'padding': '12px',
                    'fontSize': 13,
                    'fontFamily': 'Arial, sans-serif'
                },
                style_header={
                    'backgroundColor': '#27ae60',
                    'color': 'white',
                    'fontWeight': 'bold',
                    'border': '1px solid #229954'
                },
                style_data_conditional=[
                    {
                        'if': {'row_index': 'odd'},
                        'backgroundColor': '#f8f9fa'
                    }
                ],
                page_size=TABLE_PAGE_SIZE,
            ),
        ], style={
            'marginBottom': 30,
            'padding': 20,
            'backgroundColor': 'white',
            'borderRadius': 8,
            'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'
        }),
        
    ], style={
        'maxWidth': 1400, 
        'margin': 'auto', 
        'padding': 20,
        'backgroundColor': '#f5f6fa',
        'minHeight': '100vh'
    })
    
    return layout
