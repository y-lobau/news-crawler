from types import SimpleNamespace

from news_crowler.adapters.google_news import GoogleNewsAdapter
from news_crowler.models import SourceConfig


def test_google_news_builds_site_query():
    adapter = GoogleNewsAdapter(max_items=5)
    url = adapter.build_rss_url("https://example.com/news")
    assert "site%3Aexample.com" in url
    assert "news.google.com/rss/search" in url


def test_google_news_fetch_parses_entries(monkeypatch):
    adapter = GoogleNewsAdapter(max_items=1)
    source = SourceConfig(category="tech", source_url="https://example.com", title_filter_prompt="test")

    fake_feed = SimpleNamespace(
        entries=[
            SimpleNamespace(title="T1", link="https://news.google.com/articles/1", published="2026-02-28"),
            SimpleNamespace(title="T2", link="https://news.google.com/articles/2", published="2026-02-28"),
        ]
    )

    monkeypatch.setattr("news_crowler.adapters.google_news.feedparser.parse", lambda _url: fake_feed)
    rows = adapter.fetch(source)

    assert len(rows) == 1
    assert rows[0].title == "T1"
    assert rows[0].source_category == "tech"
