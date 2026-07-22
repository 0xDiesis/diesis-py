from diesis import addresses


def test_staking_address_is_checksummed() -> None:
    assert addresses.DIESIS_STAKING == "0xd1e5150000000000000000000000000000000001"


def test_multicall3_address_matches_canonical_deployment() -> None:
    assert addresses.MULTICALL3 == "0xcA11bde05977b3631167028862bE2a173976CA11"


def test_all_addresses_are_checksummed() -> None:
    from web3 import Web3

    for name in dir(addresses):
        if name.startswith("_"):
            continue
        val = getattr(addresses, name)
        if isinstance(val, str) and val.startswith("0x"):
            assert val == Web3.to_checksum_address(val), f"{name} is not checksummed"


def test_address_count() -> None:
    expected = {
        "DIESIS_STAKING",
        "DIESIS_PATRON",
        "DIESIS_CONFIG",
        "BOOTSTRAP_ORACLE",
        "BOOTSTRAP_CONFIG",
        "DIESIS_STATE_WRITER",
        "DIESIS_POSITION",
        "DIESIS_BUNDLE_ESCROW",
        "WRAPPED_DS",
        "LIQUID_STAKED_DS",
        "DIESIS_TEST_USD",
        "DIESIS_MARKETS",
        "DIESIS_SPOT_BOOK",
        "DIESIS_PERPS_BOOK",
        "DIESIS_MARGIN",
        "DIESIS_SETTLEMENT",
        "DIESIS_SETTLEMENT_ROUTER",
        "DIESIS_CONDUCTORS",
        "DIESIS_CORE_VAULT",
        "DIESIS_ISSUANCE_AUCTION",
        "DIESIS_BUYBACK_BURN",
        "DIESIS_OPERATOR_BOND",
        "DIESIS_ERC20_FACTORY",
        "DIESIS_PERP_DEPLOY",
        "DIESIS_NAME_REGISTRY",
        "DIESIS_BASE_REGISTRAR",
        "DIESIS_PUBLIC_RESOLVER",
        "DIESIS_REVERSE_REGISTRAR",
        "DIESIS_NAME_VERIFIER",
        "DIESIS_NAME_POLICY",
        "VRF",
        "STEALTH_REGISTRY",
        "STEALTH_ANNOUNCER",
        "SHIELDED_POOL",
        "PRIVACY_POOLS",
        "GROTH16_VERIFIER",
        "SECP256R1",
        "POSEIDON",
        "ML_DSA",
        "MULTICALL3",
        "PERMIT2",
    }
    actual = {n for n in dir(addresses) if not n.startswith("_")}
    assert expected == actual


def test_name_service_addresses_match_reserved_contract_slots() -> None:
    assert addresses.DIESIS_NAME_REGISTRY == "0xd1E5150000000000000000000000000000000050"
    assert addresses.DIESIS_BASE_REGISTRAR == "0xd1e5150000000000000000000000000000000051"
    assert addresses.DIESIS_PUBLIC_RESOLVER == "0xD1E5150000000000000000000000000000000052"
    assert addresses.DIESIS_REVERSE_REGISTRAR == "0xd1E5150000000000000000000000000000000053"
    assert addresses.DIESIS_NAME_VERIFIER == "0xd1e5150000000000000000000000000000000054"
    assert addresses.DIESIS_NAME_POLICY == "0xD1E5150000000000000000000000000000000055"


def test_core_vault_address_matches_solidity_precompile_slot() -> None:
    assert addresses.DIESIS_CORE_VAULT == "0x00D1E5150000000000000000000000000000C04e"
