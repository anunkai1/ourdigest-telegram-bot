# ourdigest-telegram-bot

Minimal Telegram bot that fronts the [ourdigest](https://github.com/anunkai1/ourdigest)
server. Send `/news` and it returns the latest AI/LLM digest.

Built separately from the rest of your bot fleet — does not touch tank,
mavali_eth, matrix, or any other bridge.

## Commands

| Command                | What it does                                         |
|------------------------|------------------------------------------------------|
| `/start`, `/help`      | Show help                                            |
| `/news`                | Top 5 from all topics                                |
| `/news llm`            | Top 5 from the `llm` topic                           |
| `/news ai`             | Top 5 from the `ai` topic                            |
| `/news llm 10`         | Top 10 from `llm` (max 20)                           |
| `/refresh`             | Re-pull sources from Reddit/HN/Lemmy/arXiv           |

## Requirements

- A running [ourdigest](https://github.com/anunkai1/ourdigest) server,
  reachable at the URL in `OURDIGEST_URL`.
- A Telegram bot token from [@BotFather](https://t.me/BotFather).

## Quickstart

```bash
git clone https://github.com/anunkai1/ourdigest-telegram-bot.git
cd ourdigest-telegram-bot
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

cp .env.example .env
$EDITOR .env             # set TELEGRAM_BOT_TOKEN and OURDIGEST_URL

# Smoke test — does not connect to Telegram
ourdigest-telegram-bot --smoke

# Run
ourdigest-telegram-bot
```

## systemd

```bash
sudo cp ops/ourdigest-telegram-bot/ourdigest-telegram-bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now ourdigest-telegram-bot
sudo journalctl -u ourdigest-telegram-bot -f
```

## Architecture

```
[User → /news]
    ↓
[Bot: GET http://OURDIGEST_URL/feed/all.xml]
    ↓
[Bot parses RSS, picks top N, formats Markdown]
    ↓
[Bot replies with up to N Telegram messages (split if too long)]
```

The bot is stateless. Every `/news` call pulls the latest feed from the
ourdigest server. Use `/refresh` to ask the server to re-pull from
upstream sources before reading.

## Files

```
src/ourdigest_telegram_bot/
├── __init__.py
├── bot.py          # Click entrypoint + Telegram command handlers
├── digest.py       # HTTP client for ourdigest + RSS parser
└── formatter.py    # Items → Telegram-safe Markdown messages
tests/
ops/ourdigest-telegram-bot/
├── install_runtime_venv.sh
└── ourdigest-telegram-bot.service
```

## License

MIT.
