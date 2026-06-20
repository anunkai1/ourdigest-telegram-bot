"""ourdigest HTTP client.

Fetches a topic's RSS feed and parses it into structured items. Optionally
asks the ourdigest server to refresh its sources first so /news returns
the freshest items.
"""
from __future__ import annotations

import os
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime, timezone

import httpx


@dataclass(frozen=True)
class Item:
    title: str
    link: str
    source: str
    pubdate: datetime
    summary: str = ""

    @property
    def pubdate_str(self) -> str:
        return self.pubdate.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def _text(el: ET.Element | None) -> str:
    if el is None or el.text is None:
        return ""
    return el.text.strip()


def parse_feed(xml_bytes: bytes) -> list[Item]:
    """Parse RSS 2.0 XML into a list of Items."""
    root = ET.fromstring(xml_bytes)
    items: list[Item] = []
    # RSS uses channel/item; tolerate Atom feed as future-proofing.
    channel = root.find("channel")
    if channel is None:
        return items
    for el in channel.findall("item"):
        title = _text(el.find("title"))
        link = _text(el.find("link"))
        if not title or not link:
            continue
        source = ""
        cat = el.find("category")
        if cat is not None:
            source = (cat.text or "").strip()
        pub = _text(el.find("pubDate"))
        try:
            # RFC 822: "Sun, 19 Jun 2026 04:00:00 +0000"
            from email.utils import parsedate_to_datetime
            pubdate = parsedate_to_datetime(pub).astimezone(timezone.utc) if pub else datetime.now(timezone.utc)
        except (TypeError, ValueError):
            pubdate = datetime.now(timezone.utc)
        summary = _text(el.find("description"))
        # Strip HTML for display
        import re
        summary = re.sub(r"<[^>]+>", " ", summary).strip()
        summary = re.sub(r"\s+", " ", summary)
        if len(summary) > 400:
            summary = summary[:397] + "..."
        items.append(Item(title=title, link=link, source=source, pubdate=pubdate, summary=summary))
    return items


async def refresh(base_url: str, *, timeout: float = 120.0) -> dict[str, int]:
    """Trigger ourdigest /refresh. Returns counts per topic."""
    url = base_url.rstrip("/") + "/refresh"
    async with httpx.AsyncClient(timeout=timeout) as client:
        r = await client.post(url)
        r.raise_for_status()
        return r.json().get("stories_per_topic", {})


async def fetch_topic(base_url: str, topic: str = "all", *, timeout: float = 30.0) -> list[Item]:
    """Fetch one RSS feed (topic = 'all' or a topic key)."""
    url = base_url.rstrip("/") + f"/feed/{topic}.xml"
    async with httpx.AsyncClient(timeout=timeout) as client:
        r = await client.get(url)
        r.raise_for_status()
        return parse_feed(r.content)


def get_base_url() -> str:
    return os.environ.get("OURDIGEST_URL", "http://127.0.0.1:8088").rstrip("/")
