PYTHON ?= python3

.PHONY: install test daily weekly

install:
	$(PYTHON) -m pip install -r requirements.txt

test:
	PYTHONPATH=src $(PYTHON) -m pytest -q

daily:
	PYTHONPATH=src $(PYTHON) -m news_crowler.cli daily

weekly:
	PYTHONPATH=src $(PYTHON) -m news_crowler.cli weekly
