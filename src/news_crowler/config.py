from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    notion_token: str
    notion_database_id: str = "315c08c84b45804db552fe26dc6e2e6c"
    notion_version: str = "2022-06-28"
    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "qwen2.5:7b"
    data_dir: Path = Path("data")
    rss_max_items_per_source: int = 20
    http_timeout_seconds: int = 20
    weekly_retention_days: int = 30
    weekly_window_days: int = 7
    first_run_window_days: int = 14

    @staticmethod
    def from_env() -> "Settings":
        notion_token = os.getenv("NOTION_TOKEN", "").strip()
        if not notion_token:
            raise ValueError("NOTION_TOKEN is required")

        return Settings(
            notion_token=notion_token,
            notion_database_id=os.getenv("NOTION_DATABASE_ID", "315c08c84b45804db552fe26dc6e2e6c").strip(),
            notion_version=os.getenv("NOTION_VERSION", "2022-06-28").strip(),
            ollama_base_url=os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").strip(),
            ollama_model=os.getenv("OLLAMA_MODEL", "qwen2.5:7b").strip(),
            data_dir=Path(os.getenv("DATA_DIR", "data")).expanduser(),
            rss_max_items_per_source=int(os.getenv("RSS_MAX_ITEMS_PER_SOURCE", "20")),
            http_timeout_seconds=int(os.getenv("HTTP_TIMEOUT_SECONDS", "20")),
            weekly_retention_days=int(os.getenv("WEEKLY_RETENTION_DAYS", "30")),
            weekly_window_days=int(os.getenv("WEEKLY_WINDOW_DAYS", "7")),
            first_run_window_days=int(os.getenv("FIRST_RUN_WINDOW_DAYS", "14")),
        )
