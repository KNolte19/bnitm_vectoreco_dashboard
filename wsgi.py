"""WSGI entry point for gunicorn.

Run with:
    gunicorn wsgi:application --bind 0.0.0.0:8000 --workers 4
"""
import sys
from pathlib import Path

# Ensure project root is on the path
sys.path.insert(0, str(Path(__file__).parent.absolute()))

from app import create_app

application = create_app()
