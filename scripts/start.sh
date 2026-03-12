#!/usr/bin/env sh
set -eu

HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-7860}"

export CLAFOUTIS_APP_HOST="${CLAFOUTIS_APP_HOST:-$HOST}"
export CLAFOUTIS_APP_PORT="${CLAFOUTIS_APP_PORT:-$PORT}"

exec uvicorn app.main:app \
  --app-dir app/backend \
  --host "$HOST" \
  --port "$PORT"
