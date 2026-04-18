#!/usr/bin/env bash
set -euo pipefail

HOST="${APP_HOST:-0.0.0.0}"
PORT_VALUE="${PORT:-${APP_PORT:-8000}}"

exec uvicorn app.main:app --host "$HOST" --port "$PORT_VALUE"
