"""Format a digest as a Telegram message."""
from __future__ import annotations

from html import escape

from .digest import Item


TELEGRAM_MAX = 4096


def format_digest(items: list[Item], *, topic: str, limit: int = 5) -> list[str]:
    """Return a list of Telegram-safe message strings (split if too long)."""
    items = items[:limit]
    if not items:
        return [f"No new items in {escape(topic)}."]

    chunks: list[str] = []
    current: list[str] = []
    current_len = 0

    def header_line() -> str:
        return f"ourdigest — {escape(topic)}\n{len(items)} item(s)\n\n"

    for i, it in enumerate(items, 1):
        line = (
            f"{i}. {escape(it.title)}\n"
            f"   {it.link}\n"
            f"   {escape(it.source) or 'unknown'} · {it.pubdate_str}\n"
        )
        if it.summary:
            line += f"   {escape(it.summary)}\n"
        line += "\n"

        # If appending this item would overflow and we already have content, flush.
        if current and current_len + len(line) > TELEGRAM_MAX - 64:
            chunks.append("".join(current))
            current = [header_line()]
            current_len = len(current[0])
        else:
            if not current:
                current.append(header_line())
                current_len += len(current[0])
            current.append(line)
            current_len += len(line)

    if current:
        chunks.append("".join(current))
    return chunks
