PYTHON ?= python3
VENV := .venv
BIN := $(VENV)/bin

.PHONY: venv install run check start stop status restart logs logs-api logs-tunnel

venv:
	$(PYTHON) -m venv $(VENV)

install: venv
	$(BIN)/pip install --upgrade pip
	$(BIN)/pip install -e .

run:
	$(BIN)/uvicorn app.main:app --reload

check:
	$(BIN)/python -m compileall app

start:
	chmod +x scripts/start_bot.sh
	./scripts/start_bot.sh

stop:
	chmod +x scripts/stop_bot.sh
	./scripts/stop_bot.sh

status:
	chmod +x scripts/status_bot.sh
	./scripts/status_bot.sh

restart:
	$(MAKE) stop
	$(MAKE) start

logs:
	tail -n 50 logs/api.log logs/cloudflared.log

logs-api:
	tail -n 50 logs/api.log

logs-tunnel:
	tail -n 50 logs/cloudflared.log
