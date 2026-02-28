from __future__ import annotations

import subprocess

import pytest

from news_crowler.openclaw_llm import OpenClawLLMClient


def _cp(returncode: int = 0, stdout: str = "", stderr: str = "") -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(args=["openclaw"], returncode=returncode, stdout=stdout, stderr=stderr)


def test_generate_fails_with_clear_error_when_gateway_unreachable(monkeypatch):
    monkeypatch.setattr("news_crowler.openclaw_llm.shutil.which", lambda _name: "/opt/homebrew/bin/openclaw")

    calls: list[list[str]] = []

    def _fake_run(cmd, **_kwargs):
        calls.append(cmd)
        if cmd[1] == "health":
            return _cp(returncode=1, stderr="connection refused")
        raise AssertionError("agent command should not be called when health fails")

    monkeypatch.setattr("news_crowler.openclaw_llm.subprocess.run", _fake_run)

    with pytest.raises(RuntimeError, match="OpenClaw gateway is unreachable"):
        OpenClawLLMClient(agent_id="main", timeout_seconds=10)

    assert any(cmd[1] == "health" for cmd in calls)


def test_generate_returns_payload_text(monkeypatch):
    monkeypatch.setattr("news_crowler.openclaw_llm.shutil.which", lambda _name: "/opt/homebrew/bin/openclaw")

    def _fake_run(cmd, **_kwargs):
        if cmd[1] == "health":
            return _cp(stdout='{"ok": true}')
        if cmd[1] == "agent":
            return _cp(
                stdout=(
                    '{"status":"ok","result":{"payloads":[{"text":"RELEVANT"}]}}'
                )
            )
        raise AssertionError(f"unexpected command: {cmd}")

    monkeypatch.setattr("news_crowler.openclaw_llm.subprocess.run", _fake_run)

    client = OpenClawLLMClient(agent_id="main", timeout_seconds=10)

    assert client.generate("hello") == "RELEVANT"
