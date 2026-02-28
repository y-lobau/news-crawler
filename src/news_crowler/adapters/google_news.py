from __future__ import annotations

from urllib.parse import quote_plus, urlparse

import feedparser

from news_crowler.adapters.base import SourceAdapter
from news_crowler.models import RawArticle, SourceConfig


class GoogleNewsAdapter(SourceAdapter):
    name = "google_news"

    def __init__(self, max_items: int = 20, region: str = "US", language: str = "en") -> None:
        self.max_items = max_items
        self.region = region
        self.language = language

    def supports(self, source_url: str) -> bool:
        return source_url.startswith("http://") or source_url.startswith("https://")

    def build_rss_url(self, source_url: str) -> str:
        host = urlparse(source_url).netloc
        site_query = f"site:{host}" if host else source_url
        q = quote_plus(site_query)
        return (
            "https://news.google.com/rss/search"
            f"?q={q}&hl={self.language}-{self.region}&gl={self.region}&ceid={self.region}:{self.language}"
        )

    def fetch(self, source: SourceConfig) -> list[RawArticle]:
        rss_url = self.build_rss_url(source.source_url)
        parsed = feedparser.parse(rss_url)

        articles: list[RawArticle] = []
        for entry in parsed.entries[: self.max_items]:
            title = getattr(entry, "title", "").strip()
            url = getattr(entry, "link", "").strip()
            if not title or not url:
                continue

            published = getattr(entry, "published", None)
            articles.append(
                RawArticle(
                    source_category=source.category,
                    source_url=source.source_url,
                    title=title,
                    url=url,
                    published_at=published,
                )
            )

        return articles
