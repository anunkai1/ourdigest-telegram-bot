#!/usr/bin/env bash
# Create venv and install ourdigest-telegram-bot in editable mode.
set -euo pipefail

cd "$(dirname "$0")/../.."

PY="${PYTHON:-python3}"
$PY -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e ".[dev]"

echo
echo "ourdigest-telegram-bot installed at $(pwd)/.venv"
echo "Next steps:"
echo "  cp .env.example .env  &&  edit .env (set TELEGRAM_BOT_TOKEN, OURDIGEST_URL)"
echo "  OURDIGEST_URL must point at a running ourdigest server"
echo "  .venv/bin/ourdigest-telegram-bot --smoke    # see what /news would print"
echo "  sudo cp ops/ourdigest-telegram-bot/ourdigest-telegram-bot.service /etc/systemd/system/"
echo "  sudo systemctl daemon-reload && sudo systemctl enable --now ourdigest-telegram-bot"
