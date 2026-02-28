from __future__ import annotations

import hashlib
import json
from datetime import UTC, date, datetime
from pathlib import Path


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def write_json(path: Path, data: dict | list) -> None:
    ensure_dir(path.parent)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def read_json(path: Path, default: dict | list):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def title_hash(title: str) -> str:
    return hashlib.sha256(title.strip().lower().encode("utf-8")).hexdigest()


def load_seen(path: Path) -> dict:
    data = read_json(path, {"items": {}})
    if "items" not in data:
        data = {"items": {}}
    return data


def mark_seen(seen_data: dict, title: str) -> str:
    h = title_hash(title)
    seen_data["items"][h] = {
        "title": title,
        "first_seen": datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z"),
    }
    return h


def is_seen(seen_data: dict, title: str) -> bool:
    return title_hash(title) in seen_data.get("items", {})


def daily_dir(root: Path, day: date) -> Path:
    return root / "daily" / day.isoformat()


def weekly_dir(root: Path, day: date) -> Path:
    return root / "weekly" / day.isoformat()
