import pytest

from diesis.names import (
    diesis_namehash,
    genesis_precompile_names,
    name_service_contracts,
    name_service_record_types,
    normalize_diesis_name,
    resolve_genesis_precompile_name,
    reverse_resolve_genesis_precompile,
)


def test_name_service_contracts_include_reserved_slots() -> None:
    assert name_service_contracts["registry"] == "0xd1E5150000000000000000000000000000000050"
    assert name_service_contracts["registrar"] == "0xd1e5150000000000000000000000000000000051"
    assert name_service_contracts["resolver"] == "0xD1E5150000000000000000000000000000000052"
    assert name_service_contracts["reverse_registrar"] == "0xd1E5150000000000000000000000000000000053"
    assert name_service_contracts["verifier"] == "0xd1e5150000000000000000000000000000000054"
    assert name_service_contracts["policy"] == "0xD1E5150000000000000000000000000000000055"


def test_normalize_diesis_name() -> None:
    assert normalize_diesis_name(" Alice ") == "alice.ds"
    assert normalize_diesis_name("VAULT.Project") == "vault.project.ds"
    assert normalize_diesis_name("alice.ds") == "alice.ds"


@pytest.mark.parametrize("name", ["", "ab", "-alice", "alice-", "bad_name", "alice..ds"])
def test_normalize_diesis_name_rejects_invalid_input(name: str) -> None:
    with pytest.raises(ValueError, match="Invalid .ds name"):
        normalize_diesis_name(name)


def test_diesis_namehash_returns_bytes32_hex() -> None:
    node = diesis_namehash("alice")
    assert node.startswith("0x")
    assert len(node) == 66


def test_name_service_record_types_cover_current_resolver_features() -> None:
    assert {record["id"] for record in name_service_record_types} == {
        "address",
        "text",
        "contenthash",
        "route",
        "payment",
        "agent",
        "attestation",
    }


def test_genesis_precompile_names_cover_registry_slots() -> None:
    by_key = {entry["key"]: entry for entry in genesis_precompile_names}

    assert by_key["diesis-staking"]["name"] == "diesis-staking.ds"
    assert by_key["diesis-staking"]["address"] == "0xd1e5150000000000000000000000000000000001"
    assert by_key["diesis-name-registry"]["name"] == "diesis-name-registry.ds"
    assert by_key["ml-dsa"]["address"] == "0x0000000000000000000000000000000000000300"
    assert by_key["diesis-test-usd"]["address"] == "0xD1E5150000000000000000000000000000000040"


def test_resolve_genesis_precompile_name() -> None:
    resolved = resolve_genesis_precompile_name("Diesis-Staking")

    assert resolved == {
        "key": "diesis-staking",
        "name": "diesis-staking.ds",
        "group": "staking",
        "address": "0xd1e5150000000000000000000000000000000001",
    }
    assert resolve_genesis_precompile_name("alice") is None


def test_reverse_resolve_genesis_precompile() -> None:
    assert reverse_resolve_genesis_precompile("0xD1E5150000000000000000000000000000000052") == {
        "key": "diesis-public-resolver",
        "name": "diesis-public-resolver.ds",
        "group": "names",
        "address": "0xD1E5150000000000000000000000000000000052",
    }
    assert reverse_resolve_genesis_precompile("0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb") is None
