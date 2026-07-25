import json
from pathlib import Path
from typing import Any, get_type_hints

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

ARTIFACT_DIR = Path(__file__).resolve().parents[2] / "diesis" / "contracts" / "out"


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
