# news-crowler MVP

News crawler MVP with modular source adapters, Notion source config, configurable LLM backend (OpenClaw default tokenless, Ollama, or cloud) for title relevance + summarization, and JSON-only outputs.

## Features

- Modular adapter architecture (`src/news_crowler/adapters`)
- Implemented adapter: Google News RSS (`google_news`)
- Source discovery from Notion database/page ID `315c08c84b45804db552fe26dc6e2e6c`
- Daily pipeline:
  1. Fetch sources from Notion
  2. Ingest RSS via adapters
  3. Deduplicate via JSON seen store
  4. Title-only relevance check via configured LLM backend
  5. Fulltext extraction from article URL
  6. Short summary generation
  7. Write daily JSON outputs + metrics JSON + rejected relevance debug artifact
- Weekly pipeline:
  1. Aggregate last 7 days summaries
  2. Build `digest_input.json`
  3. Write weekly metrics JSON
  4. Cleanup old daily JSON only after weekly success flag exists

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Environment variables

Required:

- `NOTION_TOKEN` - Notion integration token

Optional:

- `NOTION_DATABASE_ID` (default: `315c08c84b45804db552fe26dc6e2e6c`)
- `NOTION_VERSION` (default: `2022-06-28`)
- `LLM_BACKEND` (default: `openclaw`, options: `openclaw`, `ollama`, `cloud`)
- `OPENCLAW_AGENT_ID` (default: `main`, used when `LLM_BACKEND=openclaw`)
- `OLLAMA_BASE_URL` (default: `http://127.0.0.1:11434`)
- `OLLAMA_MODEL` (default: `qwen2.5:7b`)
- `CLOUD_LLM_BASE_URL` (default: `https://api.openai.com/v1`, used when `LLM_BACKEND=cloud`)
- `CLOUD_LLM_MODEL` (required when `LLM_BACKEND=cloud`)
- `CLOUD_LLM_API_KEY` (required when `LLM_BACKEND=cloud`)
- `LLM_TIMEOUT_SECONDS` (default: `60`)
- `DATA_DIR` (default: `data`)
- `RSS_MAX_ITEMS_PER_SOURCE` (default: `20`)
- `HTTP_TIMEOUT_SECONDS` (default: `20`)
- `WEEKLY_RETENTION_DAYS` (default: `30`)

## Run commands

Daily (default tokenless OpenClaw backend):

```bash
PYTHONPATH=src python -m news_crowler.cli daily
```

Daily with cloud LLM backend (optional compatibility mode):

```bash
export LLM_BACKEND=cloud
export CLOUD_LLM_BASE_URL=https://api.openai.com/v1
export CLOUD_LLM_MODEL=gpt-4.1-mini
export CLOUD_LLM_API_KEY=sk-...
PYTHONPATH=src python -m news_crowler.cli daily
```

Weekly:

```bash
PYTHONPATH=src python -m news_crowler.cli weekly
```

Or via make:

```bash
make daily
make weekly
```

## Tests

### Preflight for live checks

Validate live dependencies (Notion token/API + Ollama model, when Ollama checks are enabled):

```bash
make preflight
```

Skip Ollama check (weekly-only scenarios):

```bash
PYTHONPATH=src python -m news_crowler.cli preflight --skip-ollama
```

### Test targets

Run default suite (unit + mocked integration, offline deterministic):

```bash
make test
```

Run mocked integration tests only (offline deterministic):

```bash
make test-mocked
```

Run live integration tests only (real external dependencies required):

```bash
make test-live
```

Backward-compatible alias:

```bash
make test-e2e
```

### Expectation matrix

| Command | Requires internet | Requires `NOTION_TOKEN` | Requires live Notion API | Requires Ollama + model | Expected behavior |
|---|---|---|---|---|---|
| `make test` | No | No | No | No | Should pass offline; includes unit + mocked integration |
| `make test-mocked` | No | No | No | No | Should pass offline; deterministic stubbed pipeline checks |
| `make test-live` | Yes | Yes | Yes | Yes | Fails clearly if prerequisites missing; otherwise validates real daily+weekly flow |
| `make preflight` | Yes | Yes | Yes | Yes (unless `--skip-ollama`) | Reports actionable diagnostics and exits non-zero on failures |

## Output structure

- `data/seen_titles.json`
- `data/daily/YYYY-MM-DD/articles.json`
- `data/daily/YYYY-MM-DD/metrics.json`
- `data/daily/YYYY-MM-DD/rejected_by_relevance.json`
- `data/weekly/YYYY-MM-DD/digest_input.json`
- `data/weekly/YYYY-MM-DD/metrics.json`
- `data/weekly/YYYY-MM-DD/SUCCESS.flag`
