from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

from news_crowler.config import Settings
from news_crowler.storage import daily_dir, read_json, weekly_dir, write_json


def _iter_last_days(run_date: date, days: int) -> list[date]:
    return [run_date - timedelta(days=offset) for offset in range(days)]


def _cleanup_old_daily_json(settings: Settings, run_date: date) -> int:
    daily_root = settings.data_dir / "daily"
    if not daily_root.exists():
        return 0

    removed = 0
    for day_dir in daily_root.iterdir():
        if not day_dir.is_dir():
            continue
        try:
            day = date.fromisoformat(day_dir.name)
        except ValueError:
            continue

        age_days = (run_date - day).days
        if age_days <= settings.weekly_retention_days:
            continue

        for json_file in day_dir.glob("*.json"):
            json_file.unlink(missing_ok=True)
            removed += 1

    return removed


def run_weekly(settings: Settings, run_date: date | None = None) -> dict:
    run_date = run_date or date.today()
    started_at = datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")

    last_days = _iter_last_days(run_date, 7)
    digest_items: list[dict] = []
    missing_days: list[str] = []

    for day in sorted(last_days):
        articles_path = daily_dir(settings.data_dir, day) / "articles.json"
        if not articles_path.exists():
            missing_days.append(day.isoformat())
            continue

        articles = read_json(articles_path, [])
        for row in articles:
            summary = (row.get("summary") or "").strip()
            if not summary:
                continue
            digest_items.append(
                {
                    "date": day.isoformat(),
                    "category": row.get("source_category", ""),
                    "title": row.get("title", ""),
                    "url": row.get("url", ""),
                    "summary": summary,
                }
            )

    week_dir = weekly_dir(settings.data_dir, run_date)
    digest_input = {
        "run_date": run_date.isoformat(),
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "window_days": 7,
        "items": digest_items,
    }
    write_json(week_dir / "digest_input.json", digest_input)

    metrics = {
        "run_date": run_date.isoformat(),
        "started_at": started_at,
        "finished_at": datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "window_days": 7,
        "items_total": len(digest_items),
        "missing_days": missing_days,
        "cleanup_removed_files": 0,
    }
    write_json(week_dir / "metrics.json", metrics)

    success_path = week_dir / "SUCCESS.flag"
    success_path.write_text("ok\n", encoding="utf-8")

    if success_path.exists():
        removed = _cleanup_old_daily_json(settings, run_date)
        metrics["cleanup_removed_files"] = removed
        write_json(week_dir / "metrics.json", metrics)

    return {
        "digest_input_path": str(week_dir / "digest_input.json"),
        "metrics_path": str(week_dir / "metrics.json"),
        "success_flag": str(success_path),
        "metrics": metrics,
    }
