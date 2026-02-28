from __future__ import annotations

import pytest

from news_crowler.config import Settings
from news_crowler.pipelines.daily import _build_llm_client


def test_settings_from_env_defaults_to_openclaw(monkeypatch):
    monkeypatch.setenv("NOTION_TOKEN", "stub-token")
    monkeypatch.delenv("LLM_BACKEND", raising=False)

    settings = Settings.from_env()

    assert settings.llm_backend == "openclaw"


def test_settings_from_env_reads_cloud_backend(monkeypatch):
    monkeypatch.setenv("NOTION_TOKEN", "stub-token")
    monkeypatch.setenv("LLM_BACKEND", "cloud")
    monkeypatch.setenv("CLOUD_LLM_BASE_URL", "https://api.example.com/v1")
    monkeypatch.setenv("CLOUD_LLM_MODEL", "cloud-model")
    monkeypatch.setenv("CLOUD_LLM_API_KEY", "key123")

    settings = Settings.from_env()

    assert settings.llm_backend == "cloud"
    assert settings.cloud_llm_base_url == "https://api.example.com/v1"
    assert settings.cloud_llm_model == "cloud-model"
    assert settings.cloud_llm_api_key == "key123"


def test_build_llm_client_uses_openclaw_without_cloud_token(monkeypatch, tmp_path):
    settings = Settings(
        notion_token="stub-token",
        data_dir=tmp_path / "data",
        llm_backend="openclaw",
        cloud_llm_api_key="",
    )
    sentinel = object()

    monkeypatch.setattr("news_crowler.pipelines.daily.OpenClawLLMClient", lambda *_args, **_kwargs: sentinel)

    assert _build_llm_client(settings) is sentinel


def test_build_llm_client_uses_cloud_when_configured(monkeypatch, tmp_path):
    settings = Settings(
        notion_token="stub-token",
        data_dir=tmp_path / "data",
        llm_backend="cloud",
        cloud_llm_base_url="https://api.example.com/v1",
        cloud_llm_model="cloud-model",
        cloud_llm_api_key="key123",
    )
    sentinel = object()

    monkeypatch.setattr("news_crowler.pipelines.daily.CloudLLMClient", lambda *_args, **_kwargs: sentinel)

    assert _build_llm_client(settings) is sentinel


def test_build_llm_client_rejects_unknown_backend(tmp_path):
    settings = Settings(
        notion_token="stub-token",
        data_dir=tmp_path / "data",
        llm_backend="unknown",
    )

    with pytest.raises(ValueError, match="Unsupported LLM_BACKEND"):
        _build_llm_client(settings)
