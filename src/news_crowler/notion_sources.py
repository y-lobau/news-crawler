from __future__ import annotations

from dataclasses import dataclass

import requests

from news_crowler.models import SourceConfig


@dataclass
class NotionSourcesClient:
    token: str
    database_id: str
    notion_version: str = "2022-06-28"
    base_url: str = "https://api.notion.com"

    def fetch_sources(self) -> list[SourceConfig]:
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Notion-Version": self.notion_version,
            "Content-Type": "application/json",
        }
        url = f"{self.base_url}/v1/databases/{self.database_id}/query"

        out: list[SourceConfig] = []
        cursor = None

        while True:
            payload = {"page_size": 100}
            if cursor:
                payload["start_cursor"] = cursor

            response = requests.post(url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            data = response.json()

            for row in data.get("results", []):
                props = row.get("properties", {})
                category = self._property_text(props.get("category"))
                source_url = self._property_text(props.get("source URL"))
                title_filter_prompt = self._property_text(props.get("title filter prompt"))

                if source_url:
                    out.append(
                        SourceConfig(
                            category=category or "uncategorized",
                            source_url=source_url,
                            title_filter_prompt=title_filter_prompt,
                        )
                    )

            if not data.get("has_more"):
                break
            cursor = data.get("next_cursor")

        return out

    def _property_text(self, prop: dict | None) -> str:
        if not prop:
            return ""

        p_type = prop.get("type")
        if p_type == "title":
            return " ".join(item.get("plain_text", "") for item in prop.get("title", [])).strip()
        if p_type == "rich_text":
            return " ".join(item.get("plain_text", "") for item in prop.get("rich_text", [])).strip()
        if p_type == "url":
            return (prop.get("url") or "").strip()
        if p_type == "select":
            select = prop.get("select") or {}
            return (select.get("name") or "").strip()

        return ""
