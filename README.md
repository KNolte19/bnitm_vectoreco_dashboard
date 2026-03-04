# VectorEco Dashboard

A production-ready web dashboard for monitoring water container temperature measurements from environmental research stations.

## Overview

This application ingests JSON measurement files from research stations (4 containers each), stores them in a SQLite database, and provides an interactive dashboard for visualization and data quality monitoring

## Docker (recommended)

The easiest way to run the dashboard is with Docker Compose. No local Python installation is required.

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) ≥ 20.10
- [Docker Compose](https://docs.docker.com/compose/install/) ≥ 2.0

### First start

```bash
docker compose up
```

This single command will:
1. Build the Docker image and install all Python dependencies.
2. Create a named Docker volume (`vectoreco_data`) for the SQLite database, Dropbox sync-state, and file inbox/archive.
3. Initialise the database schema.
4. Download **all** JSON files from the configured Dropbox folder.
5. Ingest the downloaded files into the database.
6. Start the Gunicorn web server on port **8000**.
7. Begin polling Dropbox every **15 minutes** for new files and ingesting them automatically.

Access the dashboard at: **http://localhost:8000/dashboard/**

### Stopping and restarting

```bash
# Stop the container (data volume is preserved)
docker compose down

# Start again – only new/missing Dropbox files are downloaded and ingested
docker compose up
```

Because the Dropbox sync-state file and the database are stored on the persistent volume, a restart only fetches files that have not been seen before.

### Configuration

Create a `.env` file next to `docker-compose.yml` before starting (required for Dropbox sync):

```dotenv
# Required – Dropbox OAuth2 access token
DROPBOX_ACCESS_TOKEN=your_token_here

# Optional – Dropbox folder to sync (default: /ab_uploads/)
DROPBOX_FOLDER=/ab_uploads/

# Recommended – persistent Flask secret key (a random one is generated each
# startup if omitted, which means sessions won't survive container restarts)
SECRET_KEY=your-very-secret-key
```

Then start with:

```bash
docker compose up
```

| Environment variable     | Default                        | Description                                          |
|--------------------------|--------------------------------|------------------------------------------------------|
| `DROPBOX_ACCESS_TOKEN`   | *(empty – must be set)*        | Dropbox OAuth2 access token                          |
| `DROPBOX_FOLDER`         | `/ab_uploads/`                 | Remote Dropbox folder to sync                        |
| `SECRET_KEY`             | *(random, generated at start)* | Flask session secret key                             |
| `DEBUG`                  | `false`                        | Enable Flask debug mode                              |
| `POLL_INTERVAL_SECONDS`  | `900`                          | Dropbox sync/ingest interval in seconds (15 minutes) |

---

## Manual Installation (not recommended)

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

If you want to run the server in your local network, use:
```bash
python -m gunicorn wsgi:application --bind 0.0.0.0:8000 --workers 4
```

Then access the dashboard at: http://<your-ip-address>:8000/dashboard/

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