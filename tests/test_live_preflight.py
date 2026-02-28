import pytest

from news_crowler.live_checks import run_preflight


class _Resp:
    def __init__(self, status_code=200, payload=None):
        self.status_code = status_code
        self._payload = payload or {}

    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception(f"status={self.status_code}")

    def json(self):
        return self._payload


def test_preflight_fails_with_actionable_hints_when_token_missing_and_ollama_unreachable(monkeypatch):
    monkeypatch.delenv("NOTION_TOKEN", raising=False)
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
    monkeypatch.setenv("OLLAMA_MODEL", "qwen2.5:7b")

    def _fake_get(url, **_kwargs):
        if url.endswith("/api/tags"):
            raise RuntimeError("connection refused")
        return _Resp()

    monkeypatch.setattr("news_crowler.live_checks.requests.get", _fake_get)

    report = run_preflight(require_ollama=True, timeout_seconds=1)

    assert report["ok"] is False
    assert any("Missing NOTION_TOKEN" in check["message"] for check in report["checks"])
    assert any("Ollama check failed" in check["message"] for check in report["checks"])
    assert any("export NOTION_TOKEN=" in error for error in report["errors"])


def test_preflight_passes_when_notion_and_ollama_model_are_available(monkeypatch):
    monkeypatch.setenv("NOTION_TOKEN", "secret_stub")
    monkeypatch.setenv("NOTION_VERSION", "2022-06-28")
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
    monkeypatch.setenv("OLLAMA_MODEL", "qwen2.5:7b")

    def _fake_get(url, **_kwargs):
        if url.endswith("/v1/users/me"):
            return _Resp(payload={"object": "user"})
        if url.endswith("/api/tags"):
            return _Resp(payload={"models": [{"name": "qwen2.5:7b"}]})
        raise AssertionError(f"unexpected url: {url}")

    monkeypatch.setattr("news_crowler.live_checks.requests.get", _fake_get)

    report = run_preflight(require_ollama=True, timeout_seconds=1)

    assert report["ok"] is True
    assert all(check["ok"] for check in report["checks"])
