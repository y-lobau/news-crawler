from __future__ import annotations

import argparse
import json
from datetime import date

from news_crowler.config import Settings
from news_crowler.live_checks import run_preflight
from news_crowler.pipelines.daily import run_daily
from news_crowler.pipelines.weekly import run_weekly


def _parse_date(raw: str | None) -> date | None:
    if not raw:
        return None
    return date.fromisoformat(raw)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="news-crowler")
    sub = parser.add_subparsers(dest="command", required=True)

    daily = sub.add_parser("daily")
    daily.add_argument("--date", dest="run_date")

    weekly = sub.add_parser("weekly")
    weekly.add_argument("--date", dest="run_date")

    preflight = sub.add_parser("preflight")
    preflight.add_argument(
        "--skip-ollama",
        action="store_true",
        help="Skip Ollama/model check (useful for weekly-only validation).",
    )

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "daily":
        settings = Settings.from_env()
        result = run_daily(settings, run_date=_parse_date(args.run_date))
    elif args.command == "weekly":
        settings = Settings.from_env()
        result = run_weekly(settings, run_date=_parse_date(args.run_date))
    elif args.command == "preflight":
        result = run_preflight(require_ollama=not args.skip_ollama)
        if not result["ok"]:
            print(json.dumps(result, ensure_ascii=False, indent=2))
            raise SystemExit(2)
    else:
        raise ValueError(f"Unsupported command: {args.command}")

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
