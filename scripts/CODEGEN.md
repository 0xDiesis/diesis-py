# Qualified contract code generation

Generation requires explicit absolute `DIESIS_ARTIFACT_PREFLIGHT`,
`DIESIS_ARTIFACT_MANIFEST` and `DIESIS_ARTIFACTS_DIR`. `ABI_TYPEGEN` must explicitly select
an absolute independently qualified executable; its digest/version/source must match the
manifest. Script-free dependency installation does not install the platform binary.
The qualifier separately downloads and verifies the official binary and supplies
its explicit path; no implicit SDK or contracts executable is used. The helper recomputes manifest validity through the real
`scripts/verify-contract-artifacts.py`; missing helpers or mismatches fail closed.

`make codegen` generates all 45 Python ABI/wrapper modules and their public
re-export barrel from qualified artifacts. `make codegen-check` generates fresh
intermediates and checks byte equality without editing tracked outputs. It does
not compile, read contracts/src/abi, invoke the contracts package, or default to
an existing out directory. Python wrappers intentionally remain enabled; single
Python target output is written directly to the chosen intermediate directory.

CI invokes `qualify-contract-inputs.py` against exact contracts e905d65, on Linux
x86_64 only. It installs locked checksum-verified dependency archives, verifies
Forge 1.8.3/source cae51ad and official solc 0.8.35+47b9dedd, verifies the npm08
registry integrity/signatures/provenance and platform archive checksum, and runs
one offline source-only build through the captured compiler. Full captured inputs
and outputs are independently checked before generation. No caches, Permit2,
submodules, circuits, test compile, retry, or contracts-owned generator is used.
The Homebrew/macOS qualification and Linux CI are distinct platform records.

The portable Linux path has local fake-fixture tests; independent review,
actual Linux tool execution and hosted CI remain separate qualification gates.
Do not describe fake-fixture success as a successful compile or publication.
Root owns accepted artifact generation and publication. Preserve generated-source,
full SDK quality, consumer, provenance and independent review gates.
