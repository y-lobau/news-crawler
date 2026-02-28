from __future__ import annotations

import json
import shutil
import subprocess


class OpenClawLLMClient:
    def __init__(self, agent_id: str = "main", timeout_seconds: int = 60) -> None:
        self.agent_id = agent_id or "main"
        self.timeout_seconds = timeout_seconds
        self.model = f"openclaw:{self.agent_id}"
        self._cli = shutil.which("openclaw")
        if not self._cli:
            raise RuntimeError("OpenClaw CLI is not installed or not found in PATH.")
        self._assert_gateway_reachable()

    def _extract_json(self, raw: str) -> dict:
        text = (raw or "").strip()
        if not text:
            return {}

        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise RuntimeError(f"OpenClaw returned non-JSON output: {text[:300]}")

        blob = text[start : end + 1]
        try:
            data = json.loads(blob)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"OpenClaw returned invalid JSON: {exc}") from exc
        if not isinstance(data, dict):
            raise RuntimeError("OpenClaw returned unexpected JSON shape.")
        return data

    def _assert_gateway_reachable(self) -> None:
        proc = subprocess.run(
            [self._cli, "health", "--json", "--timeout", str(self.timeout_seconds * 1000)],
            capture_output=True,
            text=True,
            timeout=self.timeout_seconds,
            check=False,
        )
        if proc.returncode != 0:
            details = (proc.stderr or proc.stdout or "unknown error").strip()
            raise RuntimeError(f"OpenClaw gateway is unreachable: {details}")

        data = self._extract_json(proc.stdout)
        if not data.get("ok"):
            raise RuntimeError(f"OpenClaw gateway is unhealthy: {data}")

    def generate(self, prompt: str, system: str = "") -> str:
        prompt_text = prompt
        if system:
            prompt_text = f"System instructions:\n{system}\n\nUser prompt:\n{prompt}"

        proc = subprocess.run(
            [
                self._cli,
                "agent",
                "--agent",
                self.agent_id,
                "--message",
                prompt_text,
                "--json",
                "--timeout",
                str(self.timeout_seconds),
            ],
            capture_output=True,
            text=True,
            timeout=self.timeout_seconds + 5,
            check=False,
        )

        if proc.returncode != 0:
            details = (proc.stderr or proc.stdout or "unknown error").strip()
            raise RuntimeError(f"OpenClaw agent call failed: {details}")

        data = self._extract_json(proc.stdout)
        result = data.get("result") or {}
        payloads = result.get("payloads") or []
        if not payloads:
            return ""

        text = payloads[0].get("text")
        return str(text or "").strip()

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
