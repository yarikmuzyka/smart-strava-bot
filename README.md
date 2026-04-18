# Cycling Coach Bot

Telegram bot for cyclists that reads the latest Strava ride, summarizes the
session, and suggests two sensible training options for the next day.

## Stack

- Python 3.11+
- FastAPI
- Uvicorn
- Railway-ready deploy config

## Project Layout

```text
app/
  api/
  core/
  integrations/
  models/
  rules/
  schemas/
  services/
docs/
```

## Quick Start

1. Open the project folder in a terminal
2. Create the local virtual environment
3. Install dependencies
4. Copy `.env.example` to `.env`
5. Start the FastAPI server

Example:

```bash
make install
cp .env.example .env
make run
```

## Bot Lifecycle

Use these commands to manage the full local bot infrastructure:

```bash
make start
make status
make restart
make logs
make stop
```

What they do:

- `make start` starts FastAPI, starts `cloudflared`, gets a fresh public URL, and rebinds Telegram + Strava webhooks
- `make status` shows API state, tunnel state, public URL, health checks, and Telegram webhook info
- `make restart` stops everything and starts it again cleanly
- `make logs` shows the latest API and tunnel logs together
- `make logs-api` shows only the API log
- `make logs-tunnel` shows only the tunnel log
- `make stop` deletes webhooks, stops the tunnel, and stops the local API process

Important:

- `make start` uses `uvicorn` without `--reload` for stability
- if you edit code, run `make stop` and then `make start` again
- logs are written to `logs/api.log` and `logs/cloudflared.log`

If `make` is unavailable, use:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
cp .env.example .env
uvicorn app.main:app --reload
```

## First Local Run

After the server starts, open:

- `http://127.0.0.1:8000/api/v1/health`

You should see:

```json
{"status":"ok"}
```

## Strava Setup

Before testing OAuth, fill these values in `.env`:

- `APP_SECRET_KEY`
- `STRAVA_CLIENT_ID`
- `STRAVA_CLIENT_SECRET`
- `STRAVA_REDIRECT_URI`

For local development, use:

`STRAVA_REDIRECT_URI=http://localhost:8000/api/v1/auth/strava/callback`

## Current Status

This repository currently contains:

- product and architecture docs
- FastAPI backend skeleton
- initial Strava OAuth flow
- local token persistence for development
- latest activity fetch endpoint
- placeholders for Telegram integration

## Latest Ride Test

After successful Strava authorization, open:

- `http://127.0.0.1:8000/api/v1/auth/strava/latest-activity?athlete_id=YOUR_STRAVA_ATHLETE_ID`
- `http://127.0.0.1:8000/api/v1/auth/strava/latest-recommendation?athlete_id=YOUR_STRAVA_ATHLETE_ID`

The app stores Strava tokens in a local JSON file during development and uses
them to fetch your latest activity.

The recommendation endpoint now also includes:

- ride classification
- estimated fatigue signal
- 7-day ride count
- 7-day moving time and distance
- hard-ride count over the last 7 days

## Telegram Delivery Test

Add `TELEGRAM_BOT_TOKEN` to `.env`, restart the server, then send the latest
recommendation to a chat with:

- `POST http://127.0.0.1:8000/api/v1/telegram/send-latest-recommendation?athlete_id=14941878&chat_id=YOUR_CHAT_ID`

## Telegram Command MVP

To let the bot answer `/last_ride`, add this to `.env`:

- `DEFAULT_STRAVA_ATHLETE_ID=14941878`

The webhook endpoint is:

- `POST http://127.0.0.1:8000/api/v1/telegram/webhook`

For local MVP testing, you can forward Telegram updates to this endpoint with a
tunnel later, but the command handler is already in place for:

- `/start`
- `/last_ride`

## Automatic Delivery After New Strava Ride

The bot now stores the Telegram `chat_id` when you use `/start` or `/last_ride`.
After that, a new Strava `activity create` webhook can automatically trigger a
Telegram message with the latest ride analysis.

## Recommended Hosting

For a stable Telegram + Strava webhook bot, the simplest production path is
Railway.

Why Railway:

- stable public HTTPS domain
- FastAPI deploy from GitHub or CLI
- health checks and restart policy
- easy environment variable management

Relevant docs:

- [Deploy a FastAPI app on Railway](https://docs.railway.com/guides/fastapi)
- [Public networking on Railway](https://docs.railway.com/networking/public-networking)
- [Railway pricing](https://docs.railway.com/pricing)

This repo includes:

- [railway.json](/Users/ymuzyka/Documents/smart-strava-bot/railway.json)
- [scripts/start_web.sh](/Users/ymuzyka/Documents/smart-strava-bot/scripts/start_web.sh)

## Railway Deploy Checklist

1. Push this repo to GitHub.
2. Create a new Railway project.
3. Deploy from the GitHub repo.
4. In Railway, generate a public domain for the service.
5. Set the environment variables below.
6. Attach a Railway volume and mount it to `/data`.
7. Set `APP_DATA_DIR=/data`.
8. Update Strava and Telegram webhooks to the Railway domain.

Recommended Railway variables:

- `APP_ENV=production`
- `APP_DEBUG=false`
- `APP_HOST=0.0.0.0`
- `APP_PORT=8000`
- `APP_DATA_DIR=/data`
- `APP_SECRET_KEY=...`
- `TELEGRAM_BOT_TOKEN=...`
- `TELEGRAM_WEBHOOK_SECRET=...`
- `DEFAULT_STRAVA_ATHLETE_ID=14941878`
- `STRAVA_CLIENT_ID=...`
- `STRAVA_CLIENT_SECRET=...`
- `STRAVA_VERIFY_TOKEN=...`
- `STRAVA_REDIRECT_URI=https://YOUR-RAILWAY-DOMAIN/api/v1/auth/strava/callback`

Volume note:

- this MVP stores Strava tokens and Telegram chat bindings in JSON files
- without a mounted volume, those files may be lost on redeploy or restart

Webhook URLs after deploy:

- Telegram webhook:
  `https://YOUR-RAILWAY-DOMAIN/api/v1/telegram/webhook`
- Strava webhook callback:
  `https://YOUR-RAILWAY-DOMAIN/api/v1/webhooks/strava`
