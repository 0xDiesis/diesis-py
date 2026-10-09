import json
from pathlib import Path

from diesis import addresses
from diesis.chains import diesis, diesis_testnet

CANONICAL_PATH = Path(__file__).parent / "fixtures" / "sdk-canonical.json"


def _canonical() -> dict[str, object]:
    return json.loads(CANONICAL_PATH.read_text())


def _chain_shape(chain: object) -> dict[str, object]:
    return {
        "id": chain.id,
        "name": chain.name,
        "nativeCurrency": {
            "name": chain.native_currency.name,
            "symbol": chain.native_currency.symbol,
            "decimals": chain.native_currency.decimals,
        },
        "rpcUrl": chain.rpc_url,
        "explorerUrl": chain.block_explorer_url,
        "testnet": chain.testnet,
    }


def test_chain_definitions_match_typescript_sdk_contract() -> None:
    canonical = _canonical()

    assert canonical["schemaVersion"] == 1
    assert canonical["chains"] == {
        "mainnet": _chain_shape(diesis),
        "testnet": _chain_shape(diesis_testnet),
    }


def test_addresses_match_typescript_sdk_contract_case_insensitively() -> None:
    canonical_addresses = _canonical()["addresses"]
    python_addresses = {
        name: value
        for name, value in vars(addresses).items()
        if name.isupper() and isinstance(value, str) and value.startswith("0x")
    }

    assert len(canonical_addresses) == 41
    assert {name: value.lower() for name, value in canonical_addresses.items()} == {
        name: value.lower() for name, value in python_addresses.items()
    }
