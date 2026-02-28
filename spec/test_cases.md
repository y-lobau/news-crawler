# Test Cases

| ID | Type | Scenario | Expected Result |
|---|---|---|---|
| TC-UNIT-001 | unit | Core adapters/content/storage helpers | Deterministic behavior without external services |
| TC-MOCKED-DAILY-001 | mocked_integration | Daily pipeline with fake Notion/adapter/LLM + mixed article outcomes | Metrics and artifacts reflect seen filtering, relevance decisions, fulltext failures, summaries, and rejected-by-relevance debug output |
| TC-UNIT-LLM-001 | unit | Daily pipeline backend selection when `LLM_BACKEND` is unset/`openclaw`/`ollama`/`cloud` | Default uses OpenClaw, each backend selects matching client, and invalid backend fails fast |
| TC-UNIT-LLM-002 | unit | OpenClaw backend when cloud token is not provided and gateway is unavailable | Client construction does not require `CLOUD_LLM_API_KEY`; generation fails with clear gateway diagnostics |
| TC-MOCKED-WEEKLY-001 | mocked_integration | Weekly pipeline with local daily fixtures and old retained files | Digest contains only summarized items, success flag exists, old JSON cleaned after success |
| TC-MOCKED-WEEKLY-002 | mocked_integration | Weekly cleanup guard when success check is forced false | Cleanup is skipped and old files stay intact |
| TC-PREFLIGHT-001 | unit | Preflight with missing token and unreachable Ollama | Fails with actionable diagnostics for env and service reachability |
| TC-PREFLIGHT-002 | unit | Preflight with valid token + Ollama model available | Succeeds with all checks passing |
| TC-LIVE-DAILY-001 | live | Daily pipeline with real env/services | Fails clearly on missing prerequisites, otherwise writes daily artifacts |
| TC-LIVE-WEEKLY-001 | live | Daily then weekly with real env/services | Fails clearly on missing prerequisites, otherwise writes weekly digest/metrics/success flag |

## Coverage Matrix

| Test File | Covered Cases |
|---|---|
| `tests/test_daily_pipeline.py` | TC-UNIT-001 |
| `tests/test_llm_backend_switch.py` | TC-UNIT-LLM-001 |
| `tests/test_openclaw_llm.py` | TC-UNIT-LLM-002 |
| `tests/test_weekly_pipeline.py` | TC-UNIT-001 |
| `tests/test_google_news_adapter.py` | TC-UNIT-001 |
| `tests/test_mocked_integration_daily_job.py` | TC-MOCKED-DAILY-001 |
| `tests/test_mocked_integration_weekly_job.py` | TC-MOCKED-WEEKLY-001, TC-MOCKED-WEEKLY-002 |
| `tests/test_live_preflight.py` | TC-PREFLIGHT-001, TC-PREFLIGHT-002 |
| `tests/test_live_integration_daily_weekly.py` | TC-LIVE-DAILY-001, TC-LIVE-WEEKLY-001 |
