"""Tests for the RSS feed parser."""
from datetime import datetime, timezone
from email.utils import format_datetime

from ourdigest_telegram_bot.digest import parse_feed


def _rfc822(dt: datetime) -> str:
    return format_datetime(dt.astimezone(timezone.utc), usegmt=True)


def test_parse_basic_rss():
    pub = datetime(2026, 6, 19, 4, 0, 0, tzinfo=timezone.utc)
    xml = f"""<?xml version='1.0' encoding='UTF-8'?>
<rss version='2.0'>
  <channel>
    <title>LLM Digest</title>
    <item>
      <title>First item</title>
      <link>https://example.com/1</link>
      <description>Hello &amp; world</description>
      <pubDate>{_rfc822(pub)}</pubDate>
      <category>arXiv cs.LG</category>
    </item>
    <item>
      <title>Second item</title>
      <link>https://example.com/2</link>
      <description>Plain text.</description>
      <pubDate>{_rfc822(pub)}</pubDate>
    </item>
  </channel>
</rss>"""
    items = parse_feed(xml.encode())
    assert len(items) == 2
    assert items[0].title == "First item"
    assert items[0].link == "https://example.com/1"
    assert items[0].source == "arXiv cs.LG"
    assert "Hello" in items[0].summary and "&" in items[0].summary  # entities decoded
    assert items[0].pubdate.year == 2026


def test_parse_empty_channel():
    xml = "<?xml version='1.0'?><rss><channel><title>x</title></channel></rss>"
    assert parse_feed(xml.encode()) == []


def test_parse_skips_incomplete_items():
    xml = """<?xml version='1.0'?>
<rss><channel>
  <item><title>no link</title></item>
  <item><link>https://x</link></item>
</channel></rss>"""
    assert parse_feed(xml.encode()) == []
