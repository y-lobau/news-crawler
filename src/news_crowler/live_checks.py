from __future__ import annotations

import os
from dataclasses import dataclass

import requests


@dataclass(frozen=True)
class PreflightSettings:
    notion_token: str
    notion_version: str
    ollama_base_url: str
    ollama_model: str
    timeout_seconds: int

    @staticmethod
    def from_env(timeout_seconds: int = 10) -> "PreflightSettings":
        return PreflightSettings(
            notion_token=os.getenv("NOTION_TOKEN", "").strip(),
            notion_version=os.getenv("NOTION_VERSION", "2022-06-28").strip(),
            ollama_base_url=os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").strip().rstrip("/"),
            ollama_model=os.getenv("OLLAMA_MODEL", "qwen2.5:7b").strip(),
            timeout_seconds=timeout_seconds,
        )


def _check_notion(settings: PreflightSettings) -> dict:
    if not settings.notion_token:
        return {
            "name": "notion_auth",
            "ok": False,
            "message": "Missing NOTION_TOKEN. Set it before running live checks.",
            "hint": "export NOTION_TOKEN='secret_...'",
        }

    headers = {
        "Authorization": f"Bearer {settings.notion_token}",
        "Notion-Version": settings.notion_version,
    }

    try:
        response = requests.get(
            "https://api.notion.com/v1/users/me",
            headers=headers,
            timeout=settings.timeout_seconds,
        )
        response.raise_for_status()
    except Exception as exc:  # noqa: BLE001
        return {
            "name": "notion_auth",
            "ok": False,
            "message": f"Notion API check failed: {exc}",
            "hint": "Verify NOTION_TOKEN scope/integration access and outbound network reachability.",
        }

    return {
        "name": "notion_auth",
        "ok": True,
        "message": "Notion API reachable and token accepted.",
    }


def _check_ollama(settings: PreflightSettings) -> dict:
    try:
        response = requests.get(
            f"{settings.ollama_base_url}/api/tags",
            timeout=settings.timeout_seconds,
        )
        response.raise_for_status()
        data = response.json()
    except Exception as exc:  # noqa: BLE001
        return {
            "name": "ollama_model",
            "ok": False,
            "message": f"Ollama check failed: {exc}",
            "hint": f"Start Ollama and ensure {settings.ollama_base_url} is reachable.",
        }

    models = [str(item.get("name", "")).strip() for item in data.get("models", [])]
    model_names = {name for name in models if name}
    model_names_with_alias = set(model_names)
    for model_name in list(model_names):
        if model_name.endswith(":latest"):
            model_names_with_alias.add(model_name.removesuffix(":latest"))

    if settings.ollama_model not in model_names_with_alias:
        return {
            "name": "ollama_model",
            "ok": False,
            "message": (
                f"Model '{settings.ollama_model}' is not available in Ollama tags API."
            ),
            "hint": f"Run: ollama pull {settings.ollama_model}",
        }

    return {
        "name": "ollama_model",
        "ok": True,
        "message": f"Ollama reachable and model '{settings.ollama_model}' is available.",
    }


def run_preflight(*, require_ollama: bool = True, timeout_seconds: int = 10) -> dict:
    settings = PreflightSettings.from_env(timeout_seconds=timeout_seconds)
    checks: list[dict] = []
    checks.append(_check_notion(settings))

    if require_ollama:
        checks.append(_check_ollama(settings))

    errors = [f"{check['name']}: {check['message']} ({check.get('hint', 'no hint')})" for check in checks if not check["ok"]]

    return {
        "ok": len(errors) == 0,
        "require_ollama": require_ollama,
        "checks": checks,
        "errors": errors,
    }


def assert_live_prerequisites(*, require_ollama: bool = True, timeout_seconds: int = 10) -> None:
    report = run_preflight(require_ollama=require_ollama, timeout_seconds=timeout_seconds)
    if report["ok"]:
        return

    lines = [
        "Live integration prerequisites failed.",
        "Run `make preflight` for diagnostics.",
        *report["errors"],
    ]
    raise AssertionError("\n".join(lines))
