PYTHON ?= python3
VENV ?= .venv
VENV_BIN := $(VENV)/bin
DEV_READY := $(VENV)/.diesis-dev-ready

.PHONY: dev-deps codegen codegen-check lint lint-fix format format-check test typecheck quality quality-fix

$(DEV_READY): pyproject.toml
	$(PYTHON) -m venv $(VENV)
	$(VENV_BIN)/python -m pip install --disable-pip-version-check -e '.[dev]'
	touch $(DEV_READY)

dev-deps: $(DEV_READY)

codegen:
	$(PYTHON) scripts/codegen.py

codegen-check:
	$(PYTHON) scripts/codegen.py --check

lint: dev-deps
	$(VENV_BIN)/ruff check src/ tests/

lint-fix: dev-deps
	$(VENV_BIN)/ruff check src/ tests/ --fix

format: dev-deps
	$(VENV_BIN)/ruff format src/ tests/

format-check: dev-deps
	$(VENV_BIN)/ruff format --check src/ tests/

test: dev-deps
	$(VENV_BIN)/pytest tests/ -v

typecheck: dev-deps
	$(VENV_BIN)/mypy src/

quality: codegen-check lint format-check typecheck test

quality-fix: lint-fix format typecheck
