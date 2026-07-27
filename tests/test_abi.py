import json
import os
from importlib import import_module
from pathlib import Path
from typing import Any, get_type_hints

import pytest

from diesis.abi.generated import DIESISPATRON_ABI
from diesis.abi.generated.DiesisPatron import (
    DiesisPatronContract,
    DiesisPatronReservationExitSettlementV1,
    DiesisPatronReservationExitSnapshotV1,
)


def test_artifact_dir_resolver_uses_valid_explicit_contracts_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    contracts_root = tmp_path / "contracts"
    (contracts_root / "foundry.toml").parent.mkdir(parents=True)
    (contracts_root / "foundry.toml").write_text("[profile.default]\n")
    artifact_dir = contracts_root / "out"
    sentinel = artifact_dir / "DiesisConfig.sol" / "DiesisConfig.json"
    sentinel.parent.mkdir(parents=True)
    sentinel.write_text('{"abi": []}')
    monkeypatch.setenv("DIESIS_CONTRACTS_DIR", str(contracts_root))

    assert _resolve_artifact_dir(tmp_path) == artifact_dir


def test_artifact_dir_resolver_rejects_an_incomplete_explicit_contracts_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("DIESIS_CONTRACTS_DIR", str(tmp_path / "contracts"))
    with pytest.raises(FileNotFoundError, match="DIESIS_CONTRACTS_DIR"):
        _resolve_artifact_dir(tmp_path)


def test_artifact_dir_resolver_finds_the_core_node_from_a_linked_worktree(tmp_path: Path) -> None:
    worktree_tests = tmp_path / ".worktrees" / "sdk" / "tests"
    worktree_tests.mkdir(parents=True)
    node_root = tmp_path / "diesis"
    (node_root / "Cargo.toml").parent.mkdir(parents=True)
    (node_root / "Cargo.toml").write_text("[workspace]\n")
    (node_root / "contracts" / "foundry.toml").parent.mkdir(parents=True)
    (node_root / "contracts" / "foundry.toml").write_text("[profile.default]\n")
    artifact_dir = node_root / "contracts" / "out"
    sentinel = artifact_dir / "DiesisConfig.sol" / "DiesisConfig.json"
    sentinel.parent.mkdir(parents=True)
    sentinel.write_text('{"abi": []}')

    assert _resolve_artifact_dir(worktree_tests) == artifact_dir


def _is_authoritative_contracts_root(contracts_root: Path) -> bool:
    return (contracts_root / "foundry.toml").is_file() and (
        contracts_root / "out" / "DiesisConfig.sol" / "DiesisConfig.json"
    ).is_file()


def _resolve_artifact_dir(anchor: Path) -> Path:
    override = os.environ.get("DIESIS_CONTRACTS_DIR")
    if override is not None:
        contracts_root = Path(override).expanduser().resolve()
        if _is_authoritative_contracts_root(contracts_root):
            return contracts_root / "out"
        raise FileNotFoundError(f"DIESIS_CONTRACTS_DIR is not an authoritative contracts root: {contracts_root}")

    for ancestor in (anchor, *anchor.parents):
        node_root = ancestor / "diesis"
        contracts_root = node_root / "contracts"
        if (node_root / "Cargo.toml").is_file() and _is_authoritative_contracts_root(contracts_root):
            return contracts_root / "out"

    raise FileNotFoundError("unable to locate diesis/contracts/out; set DIESIS_CONTRACTS_DIR to the contracts root")


ARTIFACT_DIR = _resolve_artifact_dir(Path(__file__).resolve().parent)
CANONICAL_CONTRACT_LIST = ARTIFACT_DIR.parent / "abi-contracts.txt"


def _canonical_contract_names() -> list[str]:
    """Return the contracts both SDK generators must export."""
    return [line for line in CANONICAL_CONTRACT_LIST.read_text(encoding="utf-8").splitlines() if line]


def test_generated_bindings_match_the_canonical_contract_list() -> None:
    """Every contract selected by the shared generator list has one Python ABI module."""
    contract_names = _canonical_contract_names()
    generated_dir = Path(__file__).resolve().parents[1] / "src" / "diesis" / "abi" / "generated"
    generated_contract_names = {path.stem for path in generated_dir.glob("*.py")} - {"__init__"}

    assert len(contract_names) == len(set(contract_names))
    assert generated_contract_names == set(contract_names)


def test_generated_bindings_match_their_foundry_artifacts() -> None:
    """The canonical list drives complete ABI parity with Foundry artifacts."""
    for contract_name in _canonical_contract_names():
        module = import_module(f"diesis.abi.generated.{contract_name}")
        abi_constants = [value for name, value in vars(module).items() if name.endswith("_ABI")]
        artifact_path = ARTIFACT_DIR / f"{contract_name}.sol" / f"{contract_name}.json"

        assert len(abi_constants) == 1
        assert abi_constants[0] == json.loads(artifact_path.read_text())["abi"]


def test_patron_reservation_exit_binding_shape_matches_contract_api() -> None:
    """The generator must expose the complete reservation-exit read/write surface."""
    abi_entries = {entry["name"]: entry for entry in DIESISPATRON_ABI if "name" in entry}

    assert {
        "maxActiveReservationsPerGrant",
        "outstandingReservationExitClaims",
        "reservationExitSnapshot",
        "reservationExitSettlement",
        "withdrawReservationExit",
        "ActiveReservationLimitReached",
        "IncompleteReservationExit",
        "NoReservationExitClaim",
        "ReservationGenerationMismatch",
        "ReservationExitSnapshotted",
        "ReservationExitWithdrawn",
    } <= abi_entries.keys()

    assert get_type_hints(DiesisPatronReservationExitSnapshotV1) == {
        "detached_shares": int,
        "claimed": bool,
        "snapshotted": bool,
    }
    assert get_type_hints(DiesisPatronReservationExitSettlementV1) == {
        "grant_id": bytes,
        "total_refund": int,
        "total_detached_shares": int,
        "remaining_detached_shares": int,
        "remaining_escrow": int,
    }

    assert get_type_hints(DiesisPatronContract.max_active_reservations_per_grant)["return"] is int
    assert get_type_hints(DiesisPatronContract.outstanding_reservation_exit_claims)["return"] is int
    assert get_type_hints(DiesisPatronContract.reservation_exit_snapshot)["return"] == dict[str, Any]
    assert get_type_hints(DiesisPatronContract.reservation_exit_settlement)["return"] == dict[str, Any]
    assert get_type_hints(DiesisPatronContract.withdraw_reservation_exit)["return"] == dict[str, Any]
