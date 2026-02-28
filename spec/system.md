# News Crawler System Spec

## Scope

The system provides two production pipelines and three test modes:

- Daily pipeline: fetches sources from Notion, ingests RSS, evaluates relevance with a configured LLM backend (`openclaw`, `ollama`, or `cloud`), extracts fulltext, summarizes, writes daily JSON outputs, and writes relevance-rejection debug artifacts.
- Weekly pipeline: aggregates daily summaries for the previous 7 days, writes weekly digest inputs/metrics, writes success flag, and cleans old daily JSON after success.
- Test modes:
  - Unit tests: local-only, deterministic.
  - Mocked integration tests: pipeline-level tests with stubs/mocks and no live dependencies.
- Live integration tests: real checks against live Notion + configured LLM backend and fail if prerequisites are missing/unreachable.

## LLM Backend Rules

- Default and preferred backend is `openclaw`.
- `openclaw` backend is tokenless for cloud providers from this app perspective (no `CLOUD_LLM_API_KEY` required).
- `cloud` backend still requires explicit `CLOUD_LLM_MODEL` and `CLOUD_LLM_API_KEY`.
- If OpenClaw gateway is unreachable, daily relevance/summary calls fail with clear diagnostics.

## Live Preflight

A preflight command must verify runtime prerequisites for live runs:

- `NOTION_TOKEN` exists and authenticates against Notion API.
- Ollama endpoint is reachable.
- Configured model exists in Ollama tags when Ollama checks are required.

Preflight returns structured JSON and exits non-zero on failure.

## References

- Detailed test-case matrix: `spec/test_cases.md`
