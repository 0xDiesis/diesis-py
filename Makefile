.PHONY: codegen lint test typecheck

codegen:
	abi-typegen generate \
		--artifacts ../diesis/contracts/out \
		--out src/diesis/abi/generated \
		--target python \
		--contracts IDiesisSettlement,IDiesisSpotBook,IDiesisMarkets,DiesisStaking,DiesisPatron,DiesisConfig,IDiesisBootstrapOracle,BootstrapConfig,IDiesisPosition,ILiquidStakedDS,IWrappedDS,DiesisShieldedPool,DiesisPrivacyPools

lint:
	ruff check src/ tests/
	ruff format --check src/ tests/

test:
	pytest tests/ -v

typecheck:
	mypy src/
