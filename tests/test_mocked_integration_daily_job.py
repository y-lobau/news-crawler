import json
from datetime import date

import pytest

from news_crowler.config import Settings
from news_crowler.models import RawArticle, SourceConfig
from news_crowler.pipelines.daily import run_daily
from news_crowler.storage import title_hash, write_json


class _FakeSourcesClient:
    def fetch_sources(self):
        return [
            SourceConfig(
                category="tech",
                source_url="https://example.com/news",
                title_filter_prompt="AI news only",
            )
        ]


class _FakeAdapter:
    name = "fake"

    def supports(self, _source_url: str) -> bool:
        return True

    def fetch(self, _source: SourceConfig):
        return [
            RawArticle(
                source_category="tech",
                source_url="https://example.com/news",
                title="Seen title",
                url="https://news.example.com/seen",
                published_at="2026-02-27T10:00:00Z",
            ),
            RawArticle(
                source_category="tech",
                source_url="https://example.com/news",
                title="Irrelevant title",
                url="https://news.example.com/irrelevant",
                published_at="2026-02-27T11:00:00Z",
            ),
            RawArticle(
                source_category="tech",
                source_url="https://example.com/news",
                title="Relevant but fulltext fails",
                url="https://news.example.com/fail",
                published_at="2026-02-27T12:00:00Z",
            ),
            RawArticle(
                source_category="tech",
                source_url="https://example.com/news",
                title="Relevant and good",
                url="https://news.example.com/good",
                published_at="2026-02-27T13:00:00Z",
            ),
        ]


class _FakeOllamaClient:
    def is_title_relevant(self, title: str, _prompt_filter: str):
        if title == "Irrelevant title":
            return False, "NOT_RELEVANT"
        return True, "RELEVANT"

    def summarize(self, title: str, fulltext: str):
        return f"Summary for {title}: {fulltext[:12]}"


@pytest.mark.mocked_integration
def test_daily_job_mocked_integration_with_deterministic_stubs(monkeypatch, tmp_path):
    data_dir = tmp_path / "data"
    settings = Settings(notion_token="stub-token", data_dir=data_dir)
    run_date = date(2026, 2, 28)

    write_json(
        data_dir / "seen_titles.json",
        {
            "items": {
                title_hash("Seen title"): {
                    "title": "Seen title",
                    "first_seen": "2026-02-01T00:00:00Z",
                }
            }
        },
    )

    monkeypatch.setattr(
        "news_crowler.pipelines.daily.NotionSourcesClient",
        lambda **_kwargs: _FakeSourcesClient(),
    )
    monkeypatch.setattr(
        "news_crowler.pipelines.daily._adapter_registry",
        lambda _settings: [_FakeAdapter()],
    )
    monkeypatch.setattr(
        "news_crowler.pipelines.daily._build_llm_client",
        lambda _settings: _FakeOllamaClient(),
    )

    def _fake_extract_fulltext(url: str, timeout_seconds: int = 20) -> str:
        if url.endswith("/fail"):
            raise RuntimeError("fulltext unavailable")
        if url.endswith("/good"):
            return "Detailed article body for good item."
        return "unused"

    monkeypatch.setattr("news_crowler.pipelines.daily.extract_fulltext", _fake_extract_fulltext)

    result = run_daily(settings, run_date=run_date)

    articles_path = data_dir / "daily" / "2026-02-28" / "articles.json"
    metrics_path = data_dir / "daily" / "2026-02-28" / "metrics.json"
    rejected_path = data_dir / "daily" / "2026-02-28" / "rejected_by_relevance.json"
    seen_path = data_dir / "seen_titles.json"

    assert articles_path.exists()
    assert metrics_path.exists()
    assert rejected_path.exists()
    assert seen_path.exists()

    metrics = result["metrics"]
    assert metrics["sources_total"] == 1
    assert metrics["articles_fetched"] == 4
    assert metrics["articles_skipped_seen"] == 1
    assert metrics["articles_relevance_positive"] == 2
    assert metrics["articles_relevance_negative"] == 1
    assert metrics["articles_rejected_by_relevance"] == 1
    assert metrics["articles_fulltext_failed"] == 1
    assert metrics["articles_summarized"] == 1
    assert len(metrics["errors"]) == 1
    assert "Fulltext failed" in metrics["errors"][0]

    articles = json.loads(articles_path.read_text(encoding="utf-8"))
    assert len(articles) == 1
    assert articles[0]["title"] == "Relevant and good"
    assert articles[0]["summary"].startswith("Summary for Relevant and good")

    rejected = json.loads(rejected_path.read_text(encoding="utf-8"))
    assert len(rejected) == 1
    assert rejected[0]["title"] == "Irrelevant title"
    assert rejected[0]["url"] == "https://news.example.com/irrelevant"
    assert rejected[0]["category"] == "tech"
    assert rejected[0]["decision"] == "NOT_RELEVANT"

    seen_items = json.loads(seen_path.read_text(encoding="utf-8"))["items"]
    assert len(seen_items) == 4
