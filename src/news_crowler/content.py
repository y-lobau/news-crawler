from __future__ import annotations

from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup


def resolve_final_url(url: str, timeout_seconds: int = 20) -> str:
    host = urlparse(url).netloc
    if "news.google.com" not in host:
        return url

    try:
        response = requests.get(url, allow_redirects=True, timeout=timeout_seconds)
        return response.url or url
    except requests.RequestException:
        return url


def extract_fulltext(url: str, timeout_seconds: int = 20) -> str:
    final_url = resolve_final_url(url, timeout_seconds=timeout_seconds)

    response = requests.get(final_url, timeout=timeout_seconds)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    for bad in soup(["script", "style", "noscript"]):
        bad.decompose()

    paragraphs = [p.get_text(" ", strip=True) for p in soup.find_all("p")]
    text = "\n".join(p for p in paragraphs if len(p) > 40)
    return text[:10000]
