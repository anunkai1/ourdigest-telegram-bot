"""Tests for the digest formatter."""
from datetime import datetime, timezone

from ourdigest_telegram_bot.digest import Item
from ourdigest_telegram_bot.formatter import format_digest, TELEGRAM_MAX


def _item(title: str = "Item", link: str = "https://x", n: int = 0) -> Item:
    return Item(
        title=f"{title} {n}",
        link=f"{link}/{n}",
        source="r/Test",
        pubdate=datetime(2026, 6, 19, 4, 0, tzinfo=timezone.utc),
        summary="A" * 50,
    )


def test_empty_returns_placeholder():
    out = format_digest([], topic="llm", limit=5)
    assert len(out) == 1
    assert "llm" in out[0]
    assert "No new" in out[0]


def test_limit_caps_items():
    items = [_item(n=i) for i in range(20)]
    chunks = format_digest(items, topic="all", limit=5)
    body = "\n".join(chunks)
    assert body.count("\n1.") == 1  # only the first item marker appears once
    # First chunk lists 5 items.
    assert "1." in chunks[0] and "5." in chunks[0]
    assert "6." not in chunks[0]


def test_no_chunk_over_telegram_max():
    # Build a feed with very long summaries to force chunking.
    items = [
        Item(
            title=f"T{i}",
            link=f"https://x/{i}",
            source="s",
            pubdate=datetime(2026, 6, 19, 4, 0, tzinfo=timezone.utc),
            summary="word " * 500,  # ~2500 chars per item
        )
        for i in range(20)
    ]
    chunks = format_digest(items, topic="ai", limit=20)
    assert all(len(c) <= TELEGRAM_MAX for c in chunks)
    assert len(chunks) >= 2  # had to split


def test_special_chars_escaped():
    items = [_item(title="A & B <test>", n=0)]
    out = format_digest(items, topic="ai", limit=1)
    assert "&amp;" in out[0]
    assert "&lt;test&gt;" in out[0]
