# news-crowler MVP

News crawler MVP with modular source adapters, Notion source config, Ollama-based title relevance + summarization, and JSON-only outputs.

## Features

- Modular adapter architecture (`src/news_crowler/adapters`)
- Implemented adapter: Google News RSS (`google_news`)
- Source discovery from Notion database/page ID `314c08c84b4580509766d7ccb641dc38`
- Daily pipeline:
  1. Fetch sources from Notion
  2. Ingest RSS via adapters
  3. Deduplicate via JSON seen store
  4. Title-only relevance check using local Ollama `qwen2.5:7b`
  5. Fulltext extraction from article URL
  6. Short summary generation
  7. Write daily JSON outputs + metrics JSON
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

- `NOTION_DATABASE_ID` (default: `314c08c84b4580509766d7ccb641dc38`)
- `NOTION_VERSION` (default: `2022-06-28`)
- `OLLAMA_BASE_URL` (default: `http://127.0.0.1:11434`)
- `OLLAMA_MODEL` (default: `qwen2.5:7b`)
- `DATA_DIR` (default: `data`)
- `RSS_MAX_ITEMS_PER_SOURCE` (default: `20`)
- `HTTP_TIMEOUT_SECONDS` (default: `20`)
- `WEEKLY_RETENTION_DAYS` (default: `30`)

## Run commands

Daily:

```bash
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

## Output structure

- `data/seen_titles.json`
- `data/daily/YYYY-MM-DD/articles.json`
- `data/daily/YYYY-MM-DD/metrics.json`
- `data/weekly/YYYY-MM-DD/digest_input.json`
- `data/weekly/YYYY-MM-DD/metrics.json`
- `data/weekly/YYYY-MM-DD/SUCCESS.flag`
