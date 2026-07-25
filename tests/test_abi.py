import json
import os
from pathlib import Path
from typing import Any, get_type_hints

import pytest

from diesis.abi.generated import (
    BOOTSTRAPCONFIG_ABI,
    DIESISBASEREGISTRAR_ABI,
    DIESISCONFIG_ABI,
    DIESISCOREVAULT_ABI,
    DIESISNAMEPOLICY_ABI,
    DIESISNAMEREGISTRY_ABI,
    DIESISNAMEVERIFIER_ABI,
    DIESISPATRON_ABI,
    DIESISPRIVACYPOOLS_ABI,
    DIESISPUBLICRESOLVER_ABI,
    DIESISREVERSEREGISTRAR_ABI,
    DIESISSHIELDEDPOOL_ABI,
    DIESISSTAKING_ABI,
    IDIESISBASEREGISTRAR_ABI,
    IDIESISBOOTSTRAPORACLE_ABI,
    IDIESISBUYBACKBURN_ABI,
    IDIESISCONDUCTORS_ABI,
    IDIESISCOREVAULT_ABI,
    IDIESISERC20FACTORY_ABI,
    IDIESISISSUANCEAUCTION_ABI,
    IDIESISMARGIN_ABI,
    IDIESISMARKETS_ABI,
    IDIESISNAMEPOLICY_ABI,
    IDIESISNAMEREGISTRY_ABI,
    IDIESISNAMEVERIFIER_ABI,
    IDIESISOPERATORBOND_ABI,
    IDIESISPERPDEPLOY_ABI,
    IDIESISPERPSBOOK_ABI,
    IDIESISPOSITION_ABI,
    IDIESISPUBLICRESOLVER_ABI,
    IDIESISREVERSEREGISTRAR_ABI,
    IDIESISSETTLEMENT_ABI,
    IDIESISSPOTBOOK_ABI,
    IDIESISSTATEWRITER_ABI,
    ILIQUIDSTAKEDDS_ABI,
    IVALIDATORSHARE_ABI,
    IWRAPPEDDS_ABI,
)
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


def test_contract_abis_match_foundry_artifacts() -> None:
    abis = {
        "BootstrapConfig": BOOTSTRAPCONFIG_ABI,
        "DiesisBaseRegistrar": DIESISBASEREGISTRAR_ABI,
        "DiesisConfig": DIESISCONFIG_ABI,
        "DiesisCoreVault": DIESISCOREVAULT_ABI,
        "DiesisNamePolicy": DIESISNAMEPOLICY_ABI,
        "DiesisNameRegistry": DIESISNAMEREGISTRY_ABI,
        "DiesisNameVerifier": DIESISNAMEVERIFIER_ABI,
        "DiesisPatron": DIESISPATRON_ABI,
        "DiesisPrivacyPools": DIESISPRIVACYPOOLS_ABI,
        "DiesisPublicResolver": DIESISPUBLICRESOLVER_ABI,
        "DiesisReverseRegistrar": DIESISREVERSEREGISTRAR_ABI,
        "DiesisShieldedPool": DIESISSHIELDEDPOOL_ABI,
        "DiesisStaking": DIESISSTAKING_ABI,
        "IDiesisBaseRegistrar": IDIESISBASEREGISTRAR_ABI,
        "IDiesisBootstrapOracle": IDIESISBOOTSTRAPORACLE_ABI,
        "IDiesisBuybackBurn": IDIESISBUYBACKBURN_ABI,
        "IDiesisConductors": IDIESISCONDUCTORS_ABI,
        "IDiesisCoreVault": IDIESISCOREVAULT_ABI,
        "IDiesisErc20Factory": IDIESISERC20FACTORY_ABI,
        "IDiesisIssuanceAuction": IDIESISISSUANCEAUCTION_ABI,
        "IDiesisMargin": IDIESISMARGIN_ABI,
        "IDiesisMarkets": IDIESISMARKETS_ABI,
        "IDiesisNamePolicy": IDIESISNAMEPOLICY_ABI,
        "IDiesisNameRegistry": IDIESISNAMEREGISTRY_ABI,
        "IDiesisNameVerifier": IDIESISNAMEVERIFIER_ABI,
        "IDiesisOperatorBond": IDIESISOPERATORBOND_ABI,
        "IDiesisPerpDeploy": IDIESISPERPDEPLOY_ABI,
        "IDiesisPerpsBook": IDIESISPERPSBOOK_ABI,
        "IDiesisPosition": IDIESISPOSITION_ABI,
        "IDiesisPublicResolver": IDIESISPUBLICRESOLVER_ABI,
        "IDiesisReverseRegistrar": IDIESISREVERSEREGISTRAR_ABI,
        "IDiesisSettlement": IDIESISSETTLEMENT_ABI,
        "IDiesisSpotBook": IDIESISSPOTBOOK_ABI,
        "IDiesisStateWriter": IDIESISSTATEWRITER_ABI,
        "ILiquidStakedDS": ILIQUIDSTAKEDDS_ABI,
        "IValidatorShare": IVALIDATORSHARE_ABI,
        "IWrappedDS": IWRAPPEDDS_ABI,
    }

    assert len(abis) == 37
    for contract_name, generated_abi in abis.items():
        artifact_path = ARTIFACT_DIR / f"{contract_name}.sol" / f"{contract_name}.json"
        artifact_abi = json.loads(artifact_path.read_text())["abi"]
        assert generated_abi == artifact_abi


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
