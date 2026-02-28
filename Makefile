VENV_PYTHON := $(firstword $(wildcard .venv/bin/python3 .venv/bin/python))
PYTHON ?= $(if $(VENV_PYTHON),$(VENV_PYTHON),python3)

.PHONY: install preflight test test-mocked test-live test-e2e daily weekly

install:
	$(PYTHON) -m pip install -r requirements.txt

test:
	PYTHONPATH=src $(PYTHON) -m pytest -q -m "not live"

test-mocked:
	PYTHONPATH=src $(PYTHON) -m pytest -q -m mocked_integration

test-live:
	PYTHONPATH=src $(PYTHON) -m pytest -q -m live

test-e2e:
	$(MAKE) test-mocked

preflight:
	PYTHONPATH=src $(PYTHON) -m news_crowler.cli preflight

daily:
	PYTHONPATH=src $(PYTHON) -m news_crowler.cli daily

weekly:
	PYTHONPATH=src $(PYTHON) -m news_crowler.cli weekly
