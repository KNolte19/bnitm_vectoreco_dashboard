"""Dash application initialization and mounting."""
import dash_mantine_components as dmc
from dash import Dash
from app.dashapp.layout import create_layout
from app.dashapp.callbacks import register_callbacks


def create_dash_app(flask_app):
    """Create and configure a Dash app mounted in Flask.
    
    Args:
        flask_app: Flask application instance
        
    Returns:
        Dash application instance
    """
    dash_app = Dash(
        __name__,
        server=flask_app,
        url_base_pathname='/dashboard/',
        suppress_callback_exceptions=True
    )
    
    # Wrap layout in MantineProvider (required by dash-mantine-components)
    dash_app.layout = dmc.MantineProvider(children=create_layout())
    
    # Register callbacks
    register_callbacks(dash_app)
    
    return dash_app
