#!/bin/bash
set -e

echo "Running pending migrations..."
python scripts/upgrade_db.py

echo "Starting uvicorn..."
exec uvicorn src.app:app --host 0.0.0.0 --port 8000 --root-path "${ROOT_PATH:-}"
