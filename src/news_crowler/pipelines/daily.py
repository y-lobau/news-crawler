from __future__ import annotations

from datetime import UTC, date, datetime

from news_crowler.adapters.base import SourceAdapter
from news_crowler.adapters.google_news import GoogleNewsAdapter
from news_crowler.config import Settings
from news_crowler.content import extract_fulltext
from news_crowler.models import ProcessedArticle, SourceConfig
from news_crowler.notion_sources import NotionSourcesClient
from news_crowler.ollama import OllamaClient
from news_crowler.storage import (
    daily_dir,
    is_seen,
    load_seen,
    mark_seen,
    write_json,
)


def _adapter_registry(settings: Settings) -> list[SourceAdapter]:
    return [GoogleNewsAdapter(max_items=settings.rss_max_items_per_source)]


def _select_adapter(adapters: list[SourceAdapter], source: SourceConfig) -> SourceAdapter | None:
    for adapter in adapters:
        if adapter.supports(source.source_url):
            return adapter
    return None


def run_daily(settings: Settings, run_date: date | None = None) -> dict:
    run_date = run_date or date.today()
    started_at = datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")

    sources_client = NotionSourcesClient(
        token=settings.notion_token,
        database_id=settings.notion_database_id,
        notion_version=settings.notion_version,
    )
    ollama = OllamaClient(settings.ollama_base_url, settings.ollama_model)
    adapters = _adapter_registry(settings)

    seen_path = settings.data_dir / "seen_titles.json"
    seen_data = load_seen(seen_path)

    metrics = {
        "run_date": run_date.isoformat(),
        "started_at": started_at,
        "sources_total": 0,
        "articles_fetched": 0,
        "articles_skipped_seen": 0,
        "articles_relevance_positive": 0,
        "articles_relevance_negative": 0,
        "articles_fulltext_failed": 0,
        "articles_summarized": 0,
        "errors": [],
    }

    out_articles: list[ProcessedArticle] = []

    sources = sources_client.fetch_sources()
    metrics["sources_total"] = len(sources)

    for source in sources:
        adapter = _select_adapter(adapters, source)
        if adapter is None:
            metrics["errors"].append(f"No adapter for {source.source_url}")
            continue

        try:
            raw_articles = adapter.fetch(source)
        except Exception as exc:  # noqa: BLE001
            metrics["errors"].append(f"Adapter fetch failed for {source.source_url}: {exc}")
            continue

        metrics["articles_fetched"] += len(raw_articles)

        for raw in raw_articles:
            if is_seen(seen_data, raw.title):
                metrics["articles_skipped_seen"] += 1
                continue

            mark_seen(seen_data, raw.title)

            try:
                relevant, _reason = ollama.is_title_relevant(raw.title, source.title_filter_prompt)
            except Exception as exc:  # noqa: BLE001
                metrics["errors"].append(f"Relevance failed for '{raw.title}': {exc}")
                metrics["articles_relevance_negative"] += 1
                continue

            if not relevant:
                metrics["articles_relevance_negative"] += 1
                continue

            metrics["articles_relevance_positive"] += 1

            try:
                fulltext = extract_fulltext(raw.url, timeout_seconds=settings.http_timeout_seconds)
            except Exception as exc:  # noqa: BLE001
                metrics["articles_fulltext_failed"] += 1
                metrics["errors"].append(f"Fulltext failed for '{raw.url}': {exc}")
                continue

            if not fulltext.strip():
                metrics["articles_fulltext_failed"] += 1
                continue

            try:
                summary = ollama.summarize(raw.title, fulltext)
            except Exception as exc:  # noqa: BLE001
                metrics["errors"].append(f"Summary failed for '{raw.title}': {exc}")
                continue

            article_id = mark_seen({"items": {}}, raw.url + raw.title)
            out_articles.append(
                ProcessedArticle(
                    id=article_id,
                    source_category=raw.source_category,
                    source_url=raw.source_url,
                    title=raw.title,
                    url=raw.url,
                    published_at=raw.published_at,
                    fulltext=fulltext,
                    summary=summary,
                )
            )
            metrics["articles_summarized"] += 1

    day_dir = daily_dir(settings.data_dir, run_date)
    write_json(day_dir / "articles.json", [a.to_dict() for a in out_articles])

    metrics["finished_at"] = datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")
    write_json(day_dir / "metrics.json", metrics)
    write_json(seen_path, seen_data)

    return {
        "articles_path": str(day_dir / "articles.json"),
        "metrics_path": str(day_dir / "metrics.json"),
        "seen_path": str(seen_path),
        "metrics": metrics,
    }
