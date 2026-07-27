PYTHON ?= python3
ABI_CONTRACTS := $(shell paste -sd, ../diesis/contracts/abi-contracts.txt)

.PHONY: codegen codegen-check lint lint-fix format format-check test typecheck quality quality-fix

codegen:
	abi-typegen generate \
		--artifacts ../diesis/contracts/out \
		--out src/diesis/abi/generated \
		--target python \
		--contracts $(ABI_CONTRACTS) \
		--clean
	$(PYTHON) scripts/generate_abi_exports.py

codegen-check: codegen
	git diff --exit-code -- src/diesis/abi/generated

lint:
	ruff check src/ tests/

lint-fix:
	ruff check src/ tests/ --fix

format:
	ruff format src/ tests/

format-check:
	ruff format --check src/ tests/

test:
	pytest tests/ -v

typecheck:
	mypy src/

quality: lint format-check typecheck

quality-fix: lint-fix format typecheck
