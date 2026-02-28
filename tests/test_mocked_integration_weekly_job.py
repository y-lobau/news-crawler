import json
from datetime import date, timedelta
from pathlib import Path

import pytest

from news_crowler.config import Settings
from news_crowler.pipelines.weekly import run_weekly
from news_crowler.storage import write_json


def _create_daily_articles(data_dir: Path, day: date, rows: list[dict]) -> None:
    write_json(data_dir / "daily" / day.isoformat() / "articles.json", rows)
    write_json(data_dir / "daily" / day.isoformat() / "metrics.json", {"run_date": day.isoformat()})


@pytest.mark.mocked_integration
def test_weekly_job_mocked_integration_aggregates_digest_and_cleans_old_daily_json(tmp_path):
    data_dir = tmp_path / "data"
    run_date = date(2026, 2, 28)

    _create_daily_articles(
        data_dir,
        run_date - timedelta(days=2),
        [
            {"source_category": "tech", "title": "T1", "url": "https://a", "summary": "Summary A"},
            {"source_category": "tech", "title": "T2", "url": "https://b", "summary": "   "},
        ],
    )
    _create_daily_articles(
        data_dir,
        run_date - timedelta(days=1),
        [{"source_category": "world", "title": "T3", "url": "https://c", "summary": "Summary C"}],
    )
    _create_daily_articles(
        data_dir,
        run_date,
        [{"source_category": "finance", "title": "T4", "url": "https://d", "summary": "Summary D"}],
    )

    old_day_dir = data_dir / "daily" / "2025-12-15"
    write_json(old_day_dir / "articles.json", [{"summary": "old"}])
    write_json(old_day_dir / "metrics.json", {"old": True})

    settings = Settings(notion_token="stub-token", data_dir=data_dir, weekly_retention_days=30)
    result = run_weekly(settings, run_date=run_date)

    digest_path = data_dir / "weekly" / "2026-02-28" / "digest_input.json"
    metrics_path = data_dir / "weekly" / "2026-02-28" / "metrics.json"
    success_path = data_dir / "weekly" / "2026-02-28" / "SUCCESS.flag"

    assert digest_path.exists()
    assert metrics_path.exists()
    assert success_path.exists()
    assert result["metrics"]["items_total"] == 3
    assert result["metrics"]["cleanup_removed_files"] == 2
    assert not (old_day_dir / "articles.json").exists()
    assert not (old_day_dir / "metrics.json").exists()

    digest = json.loads(digest_path.read_text(encoding="utf-8"))
    assert digest["run_date"] == "2026-02-28"
    assert digest["window_days"] == 7
    assert [item["title"] for item in digest["items"]] == ["T1", "T3", "T4"]
    assert len(result["metrics"]["missing_days"]) == 4


@pytest.mark.mocked_integration
def test_weekly_job_mocked_integration_skips_cleanup_when_success_flag_check_fails(monkeypatch, tmp_path):
    data_dir = tmp_path / "data"
    run_date = date(2026, 2, 28)

    _create_daily_articles(
        data_dir,
        run_date,
        [{"source_category": "tech", "title": "Now", "url": "https://now", "summary": "Current"}],
    )

    old_day_dir = data_dir / "daily" / "2025-12-15"
    write_json(old_day_dir / "articles.json", [{"summary": "old"}])
    write_json(old_day_dir / "metrics.json", {"old": True})

    settings = Settings(notion_token="stub-token", data_dir=data_dir, weekly_retention_days=30)
    success_path = data_dir / "weekly" / "2026-02-28" / "SUCCESS.flag"

    original_exists = Path.exists

    def _patched_exists(self: Path) -> bool:
        if self == success_path:
            return False
        return original_exists(self)

    monkeypatch.setattr(Path, "exists", _patched_exists)

    result = run_weekly(settings, run_date=run_date)

    assert result["metrics"]["items_total"] == 1
    assert result["metrics"]["cleanup_removed_files"] == 0
    assert original_exists(old_day_dir / "articles.json")
    assert original_exists(old_day_dir / "metrics.json")
    assert original_exists(success_path)
