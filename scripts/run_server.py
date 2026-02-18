#!/usr/bin/env python3
"""Run the Flask application with embedded Dash dashboard."""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.absolute()))

from app import create_app, config

if __name__ == '__main__':
    app = create_app()
    print(f"Starting VectorEco Dashboard")
    print(f"Database: {config.DB_PATH}")
    print(f"Access dashboard at: http://localhost:5000/dashboard/")
    app.run(host='0.0.0.0', port=5000, debug=config.DEBUG)
