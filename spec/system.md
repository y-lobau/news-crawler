# News Crawler System Spec

## Scope

The system provides two production pipelines and three test modes:

- Daily pipeline: fetches sources from Notion, ingests RSS, evaluates relevance with Ollama, extracts fulltext, summarizes, and writes daily JSON outputs.
- Weekly pipeline: aggregates daily summaries for the previous 7 days, writes weekly digest inputs/metrics, writes success flag, and cleans old daily JSON after success.
- Test modes:
  - Unit tests: local-only, deterministic.
  - Mocked integration tests: pipeline-level tests with stubs/mocks and no live dependencies.
  - Live integration tests: real checks against live Notion + Ollama and fail if prerequisites are missing/unreachable.

## Live Preflight

A preflight command must verify runtime prerequisites for live runs:

- `NOTION_TOKEN` exists and authenticates against Notion API.
- Ollama endpoint is reachable.
- Configured model exists in Ollama tags when Ollama checks are required.

Preflight returns structured JSON and exits non-zero on failure.

## References

- Detailed test-case matrix: `spec/test_cases.md`
