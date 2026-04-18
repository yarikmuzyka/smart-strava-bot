#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUN_DIR="$ROOT_DIR/.run"
ENV_FILE="$ROOT_DIR/.env"
API_PID_FILE="$RUN_DIR/api.pid"
TUNNEL_PID_FILE="$RUN_DIR/cloudflared.pid"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Missing .env file."
  exit 1
fi

read_env() {
  local key="$1"
  grep "^${key}=" "$ENV_FILE" | cut -d= -f2-
}

kill_from_pid_file() {
  local pid_file="$1"
  if [[ -f "$pid_file" ]]; then
    local pid
    pid="$(cat "$pid_file")"
    if [[ -n "$pid" ]] && kill -0 "$pid" >/dev/null 2>&1; then
      kill "$pid" >/dev/null 2>&1 || true
    fi
    rm -f "$pid_file"
  fi
}

TELEGRAM_BOT_TOKEN="$(read_env TELEGRAM_BOT_TOKEN)"
STRAVA_CLIENT_ID="$(read_env STRAVA_CLIENT_ID)"
STRAVA_CLIENT_SECRET="$(read_env STRAVA_CLIENT_SECRET)"

if [[ -n "$TELEGRAM_BOT_TOKEN" ]]; then
  curl -fsS -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/deleteWebhook" \
    -d "drop_pending_updates=true" >/dev/null || true
fi

if [[ -n "$STRAVA_CLIENT_ID" && -n "$STRAVA_CLIENT_SECRET" ]]; then
  SUBSCRIPTIONS_JSON="$(curl -fsS -G "https://www.strava.com/api/v3/push_subscriptions" \
    --data-urlencode "client_id=${STRAVA_CLIENT_ID}" \
    --data-urlencode "client_secret=${STRAVA_CLIENT_SECRET}" || true)"
  mapfile -t SUB_IDS < <(printf '%s' "$SUBSCRIPTIONS_JSON" | grep -Eo '"id":[0-9]+' | cut -d: -f2 || true)
  for sub_id in "${SUB_IDS[@]}"; do
    curl -fsS -X DELETE \
      "https://www.strava.com/api/v3/push_subscriptions/${sub_id}?client_id=${STRAVA_CLIENT_ID}&client_secret=${STRAVA_CLIENT_SECRET}" \
      >/dev/null || true
  done
fi

kill_from_pid_file "$TUNNEL_PID_FILE"
kill_from_pid_file "$API_PID_FILE"

echo "Bot infrastructure is down."
