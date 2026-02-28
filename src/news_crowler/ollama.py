from __future__ import annotations

import requests


class OllamaClient:
    def __init__(self, base_url: str, model: str, timeout_seconds: int = 60) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout_seconds = timeout_seconds

    def generate(self, prompt: str, system: str = "") -> str:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "system": system,
            "stream": False,
            "options": {"temperature": 0.1},
        }
        response = requests.post(
            f"{self.base_url}/api/generate",
            json=payload,
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        data = response.json()
        return (data.get("response") or "").strip()

    def is_title_relevant(self, title: str, prompt_filter: str) -> tuple[bool, str]:
        prompt = (
            "Decide if this news title is relevant.\n"
            "Rules:\n"
            "- Use only the title.\n"
            "- Follow this relevance guidance: "
            f"{prompt_filter or 'generic relevance'}\n"
            "- Reply with only one token: RELEVANT or NOT_RELEVANT.\n\n"
            f"Title: {title}"
        )
        raw = self.generate(prompt)
        normalized = raw.strip().upper()
        return (normalized.startswith("RELEVANT"), raw)

    def summarize(self, title: str, fulltext: str) -> str:
        text = fulltext[:6000]
        prompt = (
            "Write a concise summary in 2-3 sentences.\n"
            "Do not include bullet points.\n"
            "Focus on key facts and implications.\n\n"
            f"Title: {title}\n\n"
            f"Article:\n{text}"
        )
        return self.generate(prompt)
