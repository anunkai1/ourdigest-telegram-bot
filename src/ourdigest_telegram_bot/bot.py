"""Telegram bot entrypoint.

Run with:  python -m ourdigest_telegram_bot
Smoke test: python -m ourdigest_telegram_bot --smoke
"""
from __future__ import annotations

import asyncio
import logging
import os
import sys

import click
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

from .digest import fetch_topic, get_base_url, refresh
from .formatter import format_digest

log = logging.getLogger(__name__)


HELP_TEXT = (
    "*ourdigest bot*\n\n"
    "Commands:\n"
    "  /news \\u2014 top 5 from all topics\n"
    "  /news <topic> \\u2014 top 5 from one topic (ai, llm, all)\n"
    "  /news <topic> <N> \\u2014 top N (max 20)\n"
    "  /refresh \\u2014 re-pull sources, then /news\n"
    "  /help \\u2014 this message\n"
)


def _parse_news_args(args: list[str]) -> tuple[str, int]:
    """Return (topic, limit) from /news command args."""
    topic = "all"
    limit = 5
    if args:
        first = args[0].lower()
        if first in {"ai", "llm", "all"}:
            topic = first
        else:
            try:
                limit = max(1, min(int(first), 20))
            except ValueError:
                pass
    if len(args) >= 2:
        try:
            limit = max(1, min(int(args[1]), 20))
        except ValueError:
            pass
    return topic, limit


async def _send_digest(update: Update, topic: str, limit: int) -> None:
    base = get_base_url()
    try:
        items = await fetch_topic(base, topic=topic)
    except Exception as exc:  # noqa: BLE001
        log.warning("fetch_topic(%s) failed: %s", topic, exc)
        await update.message.reply_text(
            f"_Could not reach ourdigest at {base}:_ `{exc}`",
            parse_mode="Markdown",
        )
        return

    chunks = format_digest(items, topic=topic, limit=limit)
    for chunk in chunks:
        await update.message.reply_text(chunk, parse_mode="Markdown", disable_web_page_preview=True)


async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(HELP_TEXT, parse_mode="Markdown")


async def cmd_help(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(HELP_TEXT, parse_mode="Markdown")


async def cmd_news(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    topic, limit = _parse_news_args(ctx.args or [])
    await _send_digest(update, topic, limit)


async def cmd_refresh(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    base = get_base_url()
    await update.message.reply_text(f"_Refreshing sources at {base}..._", parse_mode="Markdown")
    try:
        counts = await refresh(base, timeout=180.0)
    except Exception as exc:  # noqa: BLE001
        log.warning("refresh failed: %s", exc)
        await update.message.reply_text(f"_Refresh failed:_ `{exc}`", parse_mode="Markdown")
        return
    summary = ", ".join(f"{k}: {v}" for k, v in counts.items())
    await update.message.reply_text(f"_Refreshed._ {summary}", parse_mode="Markdown")


def build_application() -> Application:
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN env var is required")
    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("news", cmd_news))
    app.add_handler(CommandHandler("refresh", cmd_refresh))
    return app


@click.command()
@click.option("--smoke", is_flag=True, help="Don't connect to Telegram; just print what /news would send.")
@click.option("--topic", default="all", show_default=True)
@click.option("--limit", default=5, show_default=True)
def main(smoke: bool, topic: str, limit: int) -> None:
    """Run the ourdigest Telegram bot (or smoke-test it)."""
    logging.basicConfig(
        level=os.environ.get("OURDIGEST_BOT_LOG_LEVEL", "INFO"),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    if smoke:
        # Just print the digest for the requested topic without touching Telegram.
        async def _run() -> None:
            base = get_base_url()
            print(f"Fetching {base}/feed/{topic}.xml ...")
            try:
                items = await fetch_topic(base, topic=topic)
            except Exception as exc:  # noqa: BLE001
                print(f"FAILED: {exc}", file=sys.stderr)
                raise SystemExit(1)
            chunks = format_digest(items, topic=topic, limit=limit)
            print(f"\n{'-' * 60}\n".join(chunks))
            print(f"\n({len(items)} total items in feed)")

        asyncio.run(_run())
        return

    app = build_application()
    log.info("Starting ourdigest-telegram-bot (polling)")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
