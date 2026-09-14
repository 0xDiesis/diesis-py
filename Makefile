PYTHON ?= python3
ABI_CONTRACTS := $(shell paste -sd, ../diesis/contracts/abi-contracts.txt)
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
	pnpm --dir ../diesis/contracts exec abi-typegen generate \
		--artifacts $(abspath ../diesis/contracts/out) \
		--out $(abspath src/diesis/abi/generated) \
		--target python \
		--contracts $(ABI_CONTRACTS) \
		--clean
	$(PYTHON) scripts/generate_abi_exports.py

codegen-check: codegen
	git diff --exit-code -- src/diesis/abi/generated

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
