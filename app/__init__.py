"""VectorEco Dashboard application."""
from flask import Flask, redirect
from app import config


def create_app():
    """Create and configure the Flask application.
    
    Returns:
        Flask application with mounted Dash app
    """
    flask_app = Flask(__name__)
    flask_app.config['SECRET_KEY'] = config.SECRET_KEY
    flask_app.config['DEBUG'] = config.DEBUG
    
    # Root route redirects to dashboard
    @flask_app.route('/')
    def index():
        return redirect('/dashboard/')
    
    # Import and mount Dash app
    from app.dashapp import create_dash_app
    dash_app = create_dash_app(flask_app)
    
    return flask_app
