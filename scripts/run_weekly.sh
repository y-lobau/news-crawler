#!/usr/bin/env bash
set -euo pipefail

PYTHONPATH=src python -m news_crowler.cli weekly "$@"
