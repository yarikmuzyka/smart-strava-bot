#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUN_DIR="$ROOT_DIR/.run"
LOG_DIR="$ROOT_DIR/logs"
ENV_FILE="$ROOT_DIR/.env"
API_PID_FILE="$RUN_DIR/api.pid"
TUNNEL_PID_FILE="$RUN_DIR/cloudflared.pid"
TUNNEL_LOG="$LOG_DIR/cloudflared.log"

read_env() {
  local key="$1"
  grep "^${key}=" "$ENV_FILE" | cut -d= -f2-
}

port_8000_has_listener() {
  lsof -nP -iTCP:8000 -sTCP:LISTEN >/dev/null 2>&1
}

show_pid_state() {
  local label="$1"
  local pid_file="$2"
  if [[ ! -f "$pid_file" ]]; then
    echo "$label: stopped"
    return
  fi
  local pid
  pid="$(cat "$pid_file")"
  if kill -0 "$pid" >/dev/null 2>&1; then
    echo "$label: running (PID $pid)"
  else
    echo "$label: stale pid file ($pid)"
  fi
}

if port_8000_has_listener; then
  if [[ -f "$API_PID_FILE" ]]; then
    show_pid_state "API" "$API_PID_FILE"
  else
    echo "API: responding on port 8000 (external process, no pid file)"
  fi
  echo "Local health: ok"
else
  show_pid_state "API" "$API_PID_FILE"
  echo "Local health: down"
fi

show_pid_state "Tunnel" "$TUNNEL_PID_FILE"

PUBLIC_URL="$(grep -aEo 'https://[a-zA-Z0-9-]+\.trycloudflare\.com' "$TUNNEL_LOG" 2>/dev/null | tail -n1 || true)"
if [[ -n "$PUBLIC_URL" ]]; then
  echo "Public URL: $PUBLIC_URL"
  if curl -fsS "${PUBLIC_URL}/api/v1/health" >/dev/null 2>&1; then
    echo "Public health: ok"
  else
    echo "Public health: down"
  fi
else
  echo "Public URL: unknown"
fi

if [[ -f "$ENV_FILE" ]]; then
  TELEGRAM_BOT_TOKEN="$(read_env TELEGRAM_BOT_TOKEN)"
  if [[ -n "$TELEGRAM_BOT_TOKEN" ]]; then
    echo "Telegram webhook:"
    curl -fsS "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/getWebhookInfo" || true
    echo
  fi
fi
