import json
import os
from importlib import import_module
from pathlib import Path
from typing import Any, get_type_hints

import pytest
from eth_abi import encode
from web3 import Web3

from diesis.abi.generated import DIESISPATRON_ABI
from diesis.abi.generated.DiesisPatron import (
    DiesisPatronContract,
    DiesisPatronReservationExitSettlementV1,
    DiesisPatronReservationExitSnapshotV1,
)


def test_artifact_dir_resolver_requires_explicit_artifacts(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DIESIS_ARTIFACTS_DIR", raising=False)
    monkeypatch.setenv("DIESIS_CONTRACTS_DIR", str(tmp_path))
    with pytest.raises(FileNotFoundError, match="DIESIS_ARTIFACTS_DIR"):
        _resolve_artifact_dir(tmp_path)


def test_artifact_dir_resolver_accepts_existing_explicit_artifacts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("DIESIS_ARTIFACTS_DIR", str(tmp_path))
    assert _resolve_artifact_dir(tmp_path) == tmp_path.resolve()


def test_artifact_dir_resolver_rejects_missing_directory(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DIESIS_ARTIFACTS_DIR", str(tmp_path / "missing"))
    with pytest.raises(FileNotFoundError):
        _resolve_artifact_dir(tmp_path)


def _resolve_artifact_dir(anchor: Path) -> Path:
    del anchor
    override = os.environ.get("DIESIS_ARTIFACTS_DIR")
    if not override or not Path(override).is_absolute():
        raise FileNotFoundError("Explicit absolute DIESIS_ARTIFACTS_DIR required")
    root = Path(override).resolve(strict=True)
    if not root.is_dir():
        raise FileNotFoundError("DIESIS_ARTIFACTS_DIR must be a directory")
    return root


CANONICAL_CONTRACT_LIST = Path(__file__).resolve().parents[1] / "scripts/abi-contracts.txt"


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
    import subprocess
    import sys

    artifacts = _resolve_artifact_dir(Path(__file__).parent)
    manifest_path = Path(os.environ["DIESIS_ARTIFACT_MANIFEST"])
    subprocess.run(
        [
            sys.executable,
            str(Path(__file__).parents[1] / "scripts/verify-contract-artifacts.py"),
            "--preflight",
            os.environ["DIESIS_ARTIFACT_PREFLIGHT"],
            "--check",
            str(manifest_path),
        ],
        check=True,
    )
    manifest = json.loads(manifest_path.read_text())
    assert artifacts == Path(manifest["artifactRoot"]).resolve(strict=True)
    selected = {entry["contract"]: entry for entry in manifest["selectedArtifacts"]}
    assert set(selected) == set(_canonical_contract_names())
    for contract_name in _canonical_contract_names():
        module = import_module(f"diesis.abi.generated.{contract_name}")
        abi_constants = [value for name, value in vars(module).items() if name.endswith("_ABI")]
        artifact_path = artifacts / selected[contract_name]["path"]

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
    assert get_type_hints(DiesisPatronContract.reservation_exit_snapshot)["return"] == tuple[int, bool, bool]
    assert (
        get_type_hints(DiesisPatronContract.reservation_exit_settlement)["return"] == tuple[bytes, int, int, int, int]
    )
    assert get_type_hints(DiesisPatronContract.withdraw_reservation_exit)["return"] == dict[str, Any]


def test_patron_reservation_exit_results_decode_as_typed_tuples() -> None:
    patron = DiesisPatronContract(Web3.to_checksum_address("0x" + "11" * 20), Web3())
    snapshot = (123, True, False)
    settlement = (bytes.fromhex("22" * 32), 100, 80, 60, 40)

    assert (
        patron.decode_reservation_exit_snapshot_result("0x" + encode(["(uint256,bool,bool)"], [snapshot]).hex())
        == snapshot
    )
    assert (
        patron.decode_reservation_exit_settlement_result(
            "0x" + encode(["(bytes32,uint256,uint256,uint256,uint256)"], [settlement]).hex()
        )
        == settlement
    )


def test_patron_tuple_reads_and_transaction_write_use_exact_function_signatures() -> None:
    from types import SimpleNamespace
    from unittest.mock import Mock

    from web3 import Web3

    reservation = bytes.fromhex("22" * 32)
    contributor = Web3.to_checksum_address("0x" + "11" * 20)
    snapshot = (9, False, True)
    settlement = (bytes.fromhex("33" * 32), 10, 11, 12, 13)
    results = {
        "reservationExitSnapshot(bytes32,address)": snapshot,
        "reservationExitSettlement(bytes32)": settlement,
    }
    calls: list[tuple[str, tuple[Any, ...]]] = []

    def get_function(signature: str) -> Any:
        def bind(*args: Any) -> Any:
            calls.append((signature, args))
            return SimpleNamespace(
                call=lambda: results[signature],
                build_transaction=lambda transaction: {**transaction, "data": "0xfixture"},
            )

        return bind

    contract = Mock()
    contract.get_function_by_signature.side_effect = get_function
    w3 = Mock()
    w3.eth.contract.return_value = contract
    patron = DiesisPatronContract(contributor, w3)
    assert patron.reservation_exit_snapshot(reservation, contributor) == snapshot
    assert patron.reservation_exit_settlement(reservation) == settlement
    assert patron.withdraw_reservation_exit(reservation, {"from": contributor}) == {
        "from": contributor,
        "data": "0xfixture",
    }
    assert calls == [
        ("reservationExitSnapshot(bytes32,address)", (reservation, contributor)),
        ("reservationExitSettlement(bytes32)", (reservation,)),
        ("withdrawReservationExit(bytes32)", (reservation,)),
    ]
