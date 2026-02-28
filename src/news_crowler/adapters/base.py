from __future__ import annotations

from abc import ABC, abstractmethod

from news_crowler.models import RawArticle, SourceConfig


class SourceAdapter(ABC):
    name: str

    @abstractmethod
    def supports(self, source_url: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    def fetch(self, source: SourceConfig) -> list[RawArticle]:
        raise NotImplementedError
