#!/bin/bash
set -e

echo "Creating/verifying database tables..."
python scripts/create_tables.py

echo "Starting uvicorn..."
exec uvicorn src.app.main:app --host 0.0.0.0 --port 8000 --root-path "${ROOT_PATH:-}"
