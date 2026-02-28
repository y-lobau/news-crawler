from datetime import date

from news_crowler.config import Settings
from news_crowler.pipelines.daily import run_daily


class _FakeSources:
    def fetch_sources(self):
        from news_crowler.models import SourceConfig

        return [
            SourceConfig(
                category="tech",
                source_url="https://example.com",
                title_filter_prompt="AI only",
            )
        ]


class _FakeAdapter:
    name = "fake"

    def supports(self, _source_url: str) -> bool:
        return True

    def fetch(self, _source):
        from news_crowler.models import RawArticle

        return [
            RawArticle(
                source_category="tech",
                source_url="https://example.com",
                title="Interesting AI update",
                url="https://news.google.com/articles/abc",
                published_at="2026-02-28",
            )
        ]


class _FakeOllama:
    def is_title_relevant(self, _title: str, _prompt_filter: str):
        return True, "RELEVANT"

    def summarize(self, _title: str, _fulltext: str):
        return "Short summary"


def test_daily_runs_end_to_end_with_mocks(monkeypatch, tmp_path):
    settings = Settings(notion_token="x", data_dir=tmp_path / "data")

    monkeypatch.setattr("news_crowler.pipelines.daily.NotionSourcesClient", lambda **_kwargs: _FakeSources())
    monkeypatch.setattr("news_crowler.pipelines.daily._adapter_registry", lambda _settings: [_FakeAdapter()])
    monkeypatch.setattr("news_crowler.pipelines.daily._build_llm_client", lambda _settings: _FakeOllama())
    monkeypatch.setattr("news_crowler.pipelines.daily.extract_fulltext", lambda *_args, **_kwargs: "Body text")

    result = run_daily(settings, run_date=date(2026, 2, 28))

    assert result["metrics"]["sources_total"] == 1
    assert result["metrics"]["articles_summarized"] == 1
    assert result["metrics"]["llm_backend"] == "openclaw"
    assert (tmp_path / "data" / "daily" / "2026-02-28" / "articles.json").exists()
    assert (tmp_path / "data" / "daily" / "2026-02-28" / "rejected_by_relevance.json").exists()
    assert (tmp_path / "data" / "seen_titles.json").exists()
