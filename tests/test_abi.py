import json
from pathlib import Path

from diesis.abi.generated import (
    BOOTSTRAPCONFIG_ABI,
    DIESISCONFIG_ABI,
    DIESISPATRON_ABI,
    DIESISPRIVACYPOOLS_ABI,
    DIESISSHIELDEDPOOL_ABI,
    DIESISSTAKING_ABI,
    IDIESISBOOTSTRAPORACLE_ABI,
    IDIESISBUYBACKBURN_ABI,
    IDIESISCONDUCTORS_ABI,
    IDIESISERC20FACTORY_ABI,
    IDIESISISSUANCEAUCTION_ABI,
    IDIESISMARGIN_ABI,
    IDIESISMARKETS_ABI,
    IDIESISOPERATORBOND_ABI,
    IDIESISPERPDEPLOY_ABI,
    IDIESISPERPSBOOK_ABI,
    IDIESISPOSITION_ABI,
    IDIESISSETTLEMENT_ABI,
    IDIESISSPOTBOOK_ABI,
    IDIESISSTATEWRITER_ABI,
    ILIQUIDSTAKEDDS_ABI,
    IWRAPPEDDS_ABI,
)

ARTIFACT_DIR = Path(__file__).resolve().parents[2] / "diesis" / "contracts" / "out"


def test_contract_abis_match_foundry_artifacts() -> None:
    abis = {
        "BootstrapConfig": BOOTSTRAPCONFIG_ABI,
        "DiesisConfig": DIESISCONFIG_ABI,
        "DiesisPatron": DIESISPATRON_ABI,
        "DiesisPrivacyPools": DIESISPRIVACYPOOLS_ABI,
        "DiesisShieldedPool": DIESISSHIELDEDPOOL_ABI,
        "DiesisStaking": DIESISSTAKING_ABI,
        "IDiesisBootstrapOracle": IDIESISBOOTSTRAPORACLE_ABI,
        "IDiesisBuybackBurn": IDIESISBUYBACKBURN_ABI,
        "IDiesisConductors": IDIESISCONDUCTORS_ABI,
        "IDiesisErc20Factory": IDIESISERC20FACTORY_ABI,
        "IDiesisIssuanceAuction": IDIESISISSUANCEAUCTION_ABI,
        "IDiesisMargin": IDIESISMARGIN_ABI,
        "IDiesisMarkets": IDIESISMARKETS_ABI,
        "IDiesisOperatorBond": IDIESISOPERATORBOND_ABI,
        "IDiesisPerpDeploy": IDIESISPERPDEPLOY_ABI,
        "IDiesisPerpsBook": IDIESISPERPSBOOK_ABI,
        "IDiesisPosition": IDIESISPOSITION_ABI,
        "IDiesisSettlement": IDIESISSETTLEMENT_ABI,
        "IDiesisSpotBook": IDIESISSPOTBOOK_ABI,
        "IDiesisStateWriter": IDIESISSTATEWRITER_ABI,
        "ILiquidStakedDS": ILIQUIDSTAKEDDS_ABI,
        "IWrappedDS": IWRAPPEDDS_ABI,
    }

    assert len(abis) == 22
    for contract_name, generated_abi in abis.items():
        artifact_path = ARTIFACT_DIR / f"{contract_name}.sol" / f"{contract_name}.json"
        artifact_abi = json.loads(artifact_path.read_text())["abi"]
        assert generated_abi == artifact_abi
