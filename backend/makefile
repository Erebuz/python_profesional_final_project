VENV = .venv
BIN = $(VENV)/Scripts
PYTHON = $(BIN)/python

.PHONY: run lint

run:
	$(PYTHON) ./main.py

lint:
	uv run python -m pre_commit run --all-files --color=never

test:
	uv run pytest --cov=. --cov-report=html
