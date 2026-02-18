# VectorEco Dashboard

A production-ready web dashboard for monitoring water container temperature measurements from environmental research stations.

## Overview

This application ingests JSON measurement files from 20 research stations (4 containers each), stores them in a SQLite database, and provides an interactive dashboard for visualization and data quality monitoring.

## Features

- **Batch ingestion**: Process 80+ JSON files per 5-minute interval
- **Deduplication**: Automatic duplicate detection and prevention
- **Interactive dashboard**: Filter by date, location, container, and connection quality
- **Data visualization**: Seaborn-generated time series plots and gap analysis
- **Data quality monitoring**: Track missing measurement intervals
- **Production-ready**: Designed for single-machine deployment with SQLite

## Architecture

- **Flask**: Web server with application factory pattern
- **Dash**: Interactive dashboard mounted at `/dashboard/`
- **pandas**: Data handling and transformation
- **seaborn**: Statistical visualizations (rendered to PNG for Dash)
- **SQLite**: Persistent storage with uniqueness constraints

## Installation

### Prerequisites

- Python 3.8 or higher
- pip

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd bnitm_vectoreco_dashboard
```

2. Create a virtual environment (recommended):
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Initialize the database:
```bash
python scripts/init_db.py
```

This creates the SQLite database at `data/measurements.db` with the required schema and indexes.

## Usage

### Running the Dashboard

Start the Flask/Dash web application:

```bash
python scripts/run_server.py
```

Access the dashboard at: http://localhost:5000/dashboard/

### Data Ingestion

The ingestion system processes JSON files from an inbox directory. Two modes are available:

#### One-time Ingestion

Process all files in the inbox once:

```bash
python scripts/run_ingest.py --mode once
```

#### Watch Mode (Continuous)

Monitor the inbox directory and process new files automatically:

```bash
python scripts/run_ingest.py --mode watch --interval 60
```

Options:
- `--mode`: `once` or `watch` (default: once)
- `--inbox`: Inbox directory path (default: `data/inbox/`)
- `--archive`: Archive directory path (default: `data/archive/`)
- `--delete`: Delete processed files instead of archiving
- `--interval`: Watch interval in seconds (default: 60)

### Adding Measurement Data

1. Place JSON files in `data/inbox/` directory
2. Run ingestion script (or wait for watch mode to process)
3. Processed files are moved to `data/archive/`

JSON file format:
```json
{
  "sensor_id": 1,
  "container_id": 101,
  "location": "Renke Garden 1",
  "timestamp": "2024-06-01T12:00:00Z",
  "received_at": "2024-06-01T12:00:05Z",
  "temperature_water": 22.5,
  "temperature_air": 25.0,
  "connection_quality": 4
}
```

## Dashboard Features

### Filters
- **Date/Time Range**: Select measurement period
- **Locations**: Filter by research station location
- **Container IDs**: Filter by specific containers
- **Connection Quality**: Minimum quality threshold (1-4)

### Visualizations

1. **Temperature Time Series**
   - Line plot showing water and air temperatures over time
   - Interactive filtering updates the plot

2. **Latest Status Table**
   - Most recent measurement for each location/container combination
   - Shows current temperatures and connection quality

3. **Data Quality Dashboard**
   - Bar chart of missing measurement intervals
   - Table with expected vs actual measurement counts
   - Identifies gaps in data collection (based on 5-minute expected frequency)

## Database Schema

The `measurements` table stores all measurement records:

```sql
CREATE TABLE measurements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sensor_id INTEGER NOT NULL,
    container_id INTEGER NOT NULL,
    location TEXT NOT NULL,
    timestamp DATETIME NOT NULL,
    received_at DATETIME NOT NULL,
    temperature_water REAL NOT NULL,
    temperature_air REAL NOT NULL,
    connection_quality INTEGER NOT NULL,
    UNIQUE (sensor_id, container_id, timestamp)
);
```

**Uniqueness Constraint**: The combination of `(sensor_id, container_id, timestamp)` must be unique. Duplicate records are automatically ignored during ingestion.

## Project Structure

```
bnitm_vectoreco_dashboard/
├── app/
│   ├── __init__.py              # Flask app factory
│   ├── config.py                # Configuration settings
│   ├── data/
│   │   ├── db.py                # SQLite connection helper
│   │   ├── models.py            # Database schema/DDL
│   │   └── repository.py        # Query functions
│   ├── ingestion/
│   │   ├── parser.py            # JSON validation
│   │   ├── transform.py         # DataFrame conversion
│   │   └── ingest.py            # Batch processing
│   └── dashapp/
│       ├── __init__.py          # Dash app initialization
│       ├── layout.py            # Dashboard UI
│       ├── callbacks.py         # Interactive callbacks
│       └── plots.py             # Seaborn visualizations
├── scripts/
│   ├── init_db.py               # Database initialization
│   ├── run_ingest.py            # Ingestion CLI
│   └── run_server.py            # Flask server
├── tests/
│   ├── fixtures/                # Test JSON files
│   ├── test_parser.py           # Parser tests
│   └── test_deduplication.py    # Deduplication tests
├── requirements.txt             # Python dependencies
└── README.md                    # This file
```

## Testing

Run the test suite:

```bash
# Test JSON parsing and validation
python tests/test_parser.py

# Test deduplication behavior
python tests/test_deduplication.py
```

## Configuration

Configuration is managed through `app/config.py` and environment variables:

- `DB_PATH`: Database file location (default: `data/measurements.db`)
- `INBOX_DIR`: Ingestion inbox directory (default: `data/inbox/`)
- `ARCHIVE_DIR`: Processed file archive (default: `data/archive/`)
- `SECRET_KEY`: Flask secret key (default: dev key - change in production)
- `DEBUG`: Debug mode (default: False)

Set environment variables to override defaults:
```bash
export DB_PATH=/path/to/database.db
export INBOX_DIR=/path/to/inbox
export DEBUG=true
```

## Data Validation

The ingestion system validates all incoming JSON files:

- **Required fields**: All 8 fields must be present
- **Data types**: Proper type coercion (int, float, datetime)
- **Connection quality**: Must be integer in range 1-4
- **Timestamps**: Parsed as timezone-aware UTC datetimes
- **Invalid records**: Dropped and logged with reason

## Production Considerations

1. **Database Location**: Configure `DB_PATH` to a persistent location
2. **Secret Key**: Set a secure `SECRET_KEY` environment variable
3. **File Processing**: Use watch mode for continuous operation
4. **Logging**: Configure logging level via Python logging
5. **Backup**: Regularly backup the SQLite database file
6. **Monitoring**: Monitor ingestion logs for dropped/error counts

## Troubleshooting

### No data in dashboard
- Verify database exists: `ls data/measurements.db`
- Check ingestion logs for errors
- Run one-time ingestion to test: `python scripts/run_ingest.py --mode once`

### Ingestion errors
- Validate JSON format matches schema
- Check connection_quality is in range 1-4
- Ensure all required fields are present
- Review error details in ingestion output

### Dashboard not loading
- Ensure Flask server is running on port 5000
- Check for errors in server console
- Verify database is accessible

## License

[Add your license here]

## Contact

[Add contact information here]
