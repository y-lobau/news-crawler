from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class SourceConfig:
    category: str
    source_url: str
    title_filter_prompt: str


@dataclass(frozen=True)
class RawArticle:
    source_category: str
    source_url: str
    title: str
    url: str
    published_at: str | None


@dataclass(frozen=True)
class ProcessedArticle:
    id: str
    source_category: str
    source_url: str
    title: str
    url: str
    published_at: str | None
    fulltext: str
    summary: str

    def to_dict(self) -> dict:
        return asdict(self)
