from datetime import date

from news_crowler.config import Settings
from news_crowler.pipelines.weekly import run_weekly
from news_crowler.storage import write_json


def test_weekly_builds_digest_and_cleanup(tmp_path):
    data_dir = tmp_path / "data"

    day_old = data_dir / "daily" / "2025-12-01"
    write_json(
        day_old / "articles.json",
        [{"source_category": "x", "title": "old", "url": "u", "summary": "s"}],
    )
    write_json(day_old / "metrics.json", {"x": 1})

    day_recent = data_dir / "daily" / "2026-02-28"
    write_json(
        day_recent / "articles.json",
        [{"source_category": "tech", "title": "new", "url": "https://a", "summary": "summary text"}],
    )

    settings = Settings(
        notion_token="x",
        data_dir=data_dir,
        weekly_retention_days=30,
    )

    result = run_weekly(settings, run_date=date(2026, 2, 28))

    assert (data_dir / "weekly" / "2026-02-28" / "SUCCESS.flag").exists()
    assert result["metrics"]["items_total"] == 1
    assert not (day_old / "articles.json").exists()
    assert not (day_old / "metrics.json").exists()
    assert (day_recent / "articles.json").exists()
