from dataclasses import replace
from datetime import date
from pathlib import Path

import pytest

from news_crowler.config import Settings
from news_crowler.live_checks import assert_live_prerequisites
from news_crowler.pipelines.daily import run_daily
from news_crowler.pipelines.weekly import run_weekly


@pytest.mark.live
def test_live_daily_pipeline_requires_real_dependencies_and_produces_outputs(tmp_path):
    assert_live_prerequisites(require_ollama=True, timeout_seconds=8)

    settings = replace(Settings.from_env(), data_dir=tmp_path / "data")
    result = run_daily(settings, run_date=date.today())

    assert Path(result["articles_path"]).exists()
    assert Path(result["metrics_path"]).exists()
    assert Path(result["seen_path"]).exists()


@pytest.mark.live
def test_live_weekly_pipeline_after_daily_produces_digest_and_success_flag(tmp_path):
    assert_live_prerequisites(require_ollama=True, timeout_seconds=8)

    settings = replace(Settings.from_env(), data_dir=tmp_path / "data")
    run_date = date.today()
    run_daily(settings, run_date=run_date)
    result = run_weekly(settings, run_date=run_date)

    assert Path(result["digest_input_path"]).exists()
    assert Path(result["metrics_path"]).exists()
    assert Path(result["success_flag"]).exists()
