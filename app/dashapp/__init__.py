"""Dash application initialization and mounting."""
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
    
    # Set layout
    dash_app.layout = create_layout()
    
    # Register callbacks
    register_callbacks(dash_app)
    
    return dash_app
