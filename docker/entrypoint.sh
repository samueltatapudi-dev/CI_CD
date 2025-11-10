#!/bin/sh
set -eu

APP_VERSION=${APP_VERSION:-ACEest_Fitness}
PORT=${PORT:-8000}
RUNNER=${RUNNER:-gunicorn}
WORKERS=${WORKERS:-2}

APP_DIR="/app/flask_apps/${APP_VERSION}"
APP_FILE="${APP_DIR}/app.py"

if [ ! -f "$APP_FILE" ]; then
  echo "[ERROR] Could not find $APP_FILE"
  echo "Available versions under /app/flask_apps:"
  ls -1 /app/flask_apps || true
  exit 1
fi

echo "Starting '${APP_VERSION}' on port ${PORT} using ${RUNNER}..."

if [ "$RUNNER" = "flask" ]; then
  # Use Flask development server
  exec python -m flask --app "$APP_FILE" run --host 0.0.0.0 --port "$PORT"
else
  # Use gunicorn application server
  # Change working dir so relative template paths resolve
  exec gunicorn --chdir "$APP_DIR" "app:app" -b 0.0.0.0:"$PORT" --workers "$WORKERS"
fi

