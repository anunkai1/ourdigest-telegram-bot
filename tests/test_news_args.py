"""Test /news argument parsing."""
from ourdigest_telegram_bot.bot import _parse_news_args


def test_defaults():
    assert _parse_news_args([]) == ("all", 5)


def test_topic_only():
    assert _parse_news_args(["llm"]) == ("llm", 5)
    assert _parse_news_args(["ai"]) == ("ai", 5)
    assert _parse_news_args(["all"]) == ("all", 5)


def test_topic_and_limit():
    assert _parse_news_args(["llm", "10"]) == ("llm", 10)


def test_limit_only():
    assert _parse_news_args(["7"]) == ("all", 7)


def test_limit_clamped():
    assert _parse_news_args(["999"])[1] == 20  # capped at 20
    assert _parse_news_args(["0"])[1] == 1  # floored at 1


def test_garbage_falls_back():
    assert _parse_news_args(["nope"]) == ("all", 5)
