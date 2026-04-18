#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUN_DIR="$ROOT_DIR/.run"
LOG_DIR="$ROOT_DIR/logs"
ENV_FILE="$ROOT_DIR/.env"
API_LOG="$LOG_DIR/api.log"
TUNNEL_LOG="$LOG_DIR/cloudflared.log"
API_PID_FILE="$RUN_DIR/api.pid"
TUNNEL_PID_FILE="$RUN_DIR/cloudflared.pid"

mkdir -p "$RUN_DIR" "$LOG_DIR"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Missing .env file. Create it from .env.example first."
  exit 1
fi

if [[ ! -x "$ROOT_DIR/.venv/bin/uvicorn" ]]; then
  echo "Missing .venv or uvicorn. Run 'make install' first."
  exit 1
fi

if ! command -v cloudflared >/dev/null 2>&1; then
  echo "cloudflared is not installed."
  exit 1
fi

read_env() {
  local key="$1"
  grep "^${key}=" "$ENV_FILE" | cut -d= -f2-
}

is_pid_alive() {
  local pid="$1"
  kill -0 "$pid" >/dev/null 2>&1
}

port_8000_has_listener() {
  lsof -nP -iTCP:8000 -sTCP:LISTEN >/dev/null 2>&1
}

get_public_url() {
  grep -aEo 'https://[a-zA-Z0-9-]+\.trycloudflare\.com' "$TUNNEL_LOG" 2>/dev/null | tail -n1 || true
}

public_url_is_reachable() {
  local url="$1"
  [[ -n "$url" ]] || return 1
  curl -fsS --connect-timeout 5 --max-time 10 "${url}/api/v1/health" >/dev/null 2>&1
}

start_tunnel() {
  : >"$TUNNEL_LOG"
  nohup cloudflared tunnel --protocol http2 --url http://127.0.0.1:8000 >"$TUNNEL_LOG" 2>&1 &
  echo "$!" >"$TUNNEL_PID_FILE"
}

stop_tunnel() {
  if [[ -f "$TUNNEL_PID_FILE" ]]; then
    local pid
    pid="$(cat "$TUNNEL_PID_FILE")"
    if [[ -n "$pid" ]] && is_pid_alive "$pid"; then
      kill "$pid" >/dev/null 2>&1 || true
    fi
    rm -f "$TUNNEL_PID_FILE"
  fi
}

cleanup_stale_pid() {
  local pid_file="$1"
  if [[ -f "$pid_file" ]]; then
    local pid
    pid="$(cat "$pid_file")"
    if [[ -n "$pid" ]] && ! is_pid_alive "$pid"; then
      rm -f "$pid_file"
    fi
  fi
}

cleanup_stale_pid "$API_PID_FILE"
cleanup_stale_pid "$TUNNEL_PID_FILE"

if [[ -f "$API_PID_FILE" ]]; then
  echo "API already running with PID $(cat "$API_PID_FILE")"
elif port_8000_has_listener; then
  echo "API already responding on port 8000, reusing it."
else
  nohup "$ROOT_DIR/.venv/bin/uvicorn" app.main:app --host 127.0.0.1 --port 8000 >"$API_LOG" 2>&1 &
  echo "$!" >"$API_PID_FILE"
fi

for _ in {1..20}; do
  if port_8000_has_listener; then
    break
  fi
  sleep 1
done

if ! port_8000_has_listener; then
  echo "API failed to start on port 8000. See $API_LOG"
  exit 1
fi

if [[ -f "$TUNNEL_PID_FILE" ]]; then
  echo "Tunnel already running with PID $(cat "$TUNNEL_PID_FILE")"
  EXISTING_PUBLIC_URL="$(get_public_url)"
  if ! public_url_is_reachable "$EXISTING_PUBLIC_URL"; then
    echo "Existing tunnel is not reachable, restarting it."
    stop_tunnel
    start_tunnel
  fi
else
  start_tunnel
fi

PUBLIC_URL=""
for _ in {1..45}; do
  PUBLIC_URL="$(get_public_url)"
  if [[ -n "$PUBLIC_URL" ]]; then
    break
  fi
  sleep 1
done

if [[ -z "$PUBLIC_URL" ]]; then
  echo "Failed to get cloudflared public URL. See $TUNNEL_LOG"
  exit 1
fi

for _ in {1..45}; do
  if public_url_is_reachable "$PUBLIC_URL"; then
    break
  fi
  sleep 2
done

if ! public_url_is_reachable "$PUBLIC_URL"; then
  echo "Public tunnel URL did not become reachable in time: $PUBLIC_URL"
  echo "See $TUNNEL_LOG"
  exit 1
fi

TELEGRAM_BOT_TOKEN="$(read_env TELEGRAM_BOT_TOKEN)"
TELEGRAM_WEBHOOK_SECRET="$(read_env TELEGRAM_WEBHOOK_SECRET)"
STRAVA_CLIENT_ID="$(read_env STRAVA_CLIENT_ID)"
STRAVA_CLIENT_SECRET="$(read_env STRAVA_CLIENT_SECRET)"
STRAVA_VERIFY_TOKEN="$(read_env STRAVA_VERIFY_TOKEN)"

if [[ -n "$TELEGRAM_BOT_TOKEN" ]]; then
  TELEGRAM_RESPONSE="$(curl -sS -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/setWebhook" \
    --data-urlencode "url=${PUBLIC_URL}/api/v1/telegram/webhook" \
    --data-urlencode "secret_token=${TELEGRAM_WEBHOOK_SECRET}")"
  if [[ "$TELEGRAM_RESPONSE" != *'"ok":true'* ]]; then
    echo "Failed to set Telegram webhook:"
    echo "$TELEGRAM_RESPONSE"
    exit 1
  fi
fi

if [[ -n "$STRAVA_CLIENT_ID" && -n "$STRAVA_CLIENT_SECRET" && -n "$STRAVA_VERIFY_TOKEN" ]]; then
  SUBSCRIPTIONS_JSON="$(curl -fsS -G "https://www.strava.com/api/v3/push_subscriptions" \
    --data-urlencode "client_id=${STRAVA_CLIENT_ID}" \
    --data-urlencode "client_secret=${STRAVA_CLIENT_SECRET}")"
  mapfile -t SUB_IDS < <(printf '%s' "$SUBSCRIPTIONS_JSON" | grep -Eo '"id":[0-9]+' | cut -d: -f2)
  for sub_id in "${SUB_IDS[@]}"; do
    curl -fsS -X DELETE \
      "https://www.strava.com/api/v3/push_subscriptions/${sub_id}?client_id=${STRAVA_CLIENT_ID}&client_secret=${STRAVA_CLIENT_SECRET}" \
      >/dev/null
  done
  STRAVA_RESPONSE="$(curl -sS -X POST "https://www.strava.com/api/v3/push_subscriptions" \
    -d "client_id=${STRAVA_CLIENT_ID}" \
    -d "client_secret=${STRAVA_CLIENT_SECRET}" \
    -d "callback_url=${PUBLIC_URL}/api/v1/webhooks/strava" \
    -d "verify_token=${STRAVA_VERIFY_TOKEN}")"
  if [[ "$STRAVA_RESPONSE" != *'"id":'* ]]; then
    echo "Failed to create Strava webhook subscription:"
    echo "$STRAVA_RESPONSE"
    exit 1
  fi
fi

echo "Bot infrastructure is up."
echo "Public URL: $PUBLIC_URL"
echo "API log: $API_LOG"
echo "Tunnel log: $TUNNEL_LOG"
