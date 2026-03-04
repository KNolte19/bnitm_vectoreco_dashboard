#!/bin/bash
# entrypoint.sh – orchestrates startup for the VectorEco dashboard container.
#
# Workflow (identical for first start and subsequent restarts):
#   1. Initialise the database (idempotent – uses CREATE TABLE IF NOT EXISTS).
#   2. Sync new/missing JSON files from Dropbox (state file in the volume
#      ensures already-downloaded files are never re-fetched).
#   3. Ingest all files now in the inbox.
#   4. Launch a background loop that repeats steps 2–3 every 15 minutes.
#   5. Start Gunicorn in the foreground (PID 1 receives SIGTERM on compose-down).

set -euo pipefail

POLL_INTERVAL=${POLL_INTERVAL_SECONDS:-900}   # default: 15 minutes

# Generate a random SECRET_KEY at runtime if one was not injected
if [ -z "${SECRET_KEY:-}" ]; then
  export SECRET_KEY
  SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")
  echo "==> Generated a random SECRET_KEY for this session."
fi

cd /app

echo "==> Initialising database..."
python scripts/init_db.py

echo "==> Running initial Dropbox sync..."
python scripts/sync_dropbox.py --once

echo "==> Running initial ingestion..."
python scripts/run_ingest.py --mode once

# Background sync-and-ingest loop
(
  while true; do
    sleep "${POLL_INTERVAL}"
    echo "==> [background] Running Dropbox sync..."
    python scripts/sync_dropbox.py --once
    echo "==> [background] Running ingestion..."
    python scripts/run_ingest.py --mode once
  done
) &

echo "==> Starting Gunicorn on port 8000..."
exec gunicorn wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers 2 \
  --timeout 120 \
  --access-logfile - \
  --error-logfile -
