PYTHON ?= python3

.PHONY: codegen lint lint-fix format format-check test typecheck quality quality-fix

codegen:
	abi-typegen generate \
		--artifacts ../diesis/contracts/out \
		--out src/diesis/abi/generated \
		--target python \
		--contracts IDiesisSettlement,IDiesisSpotBook,IDiesisPerpsBook,IDiesisMargin,IDiesisMarkets,IDiesisStateWriter,IDiesisConductors,IDiesisIssuanceAuction,IDiesisBuybackBurn,IDiesisOperatorBond,IDiesisErc20Factory,IDiesisPerpDeploy,DiesisStaking,DiesisPatron,DiesisConfig,IDiesisBootstrapOracle,BootstrapConfig,IDiesisPosition,ILiquidStakedDS,IWrappedDS,DiesisShieldedPool,DiesisPrivacyPools \
		--clean
	$(PYTHON) scripts/generate_abi_exports.py

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
