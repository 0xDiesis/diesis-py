from diesis import addresses


def test_staking_address_is_checksummed() -> None:
    assert addresses.DIESIS_STAKING == "0xd1e5150000000000000000000000000000000001"


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
        "WRAPPED_DS",
        "LIQUID_STAKED_DS",
        "DIESIS_MARKETS",
        "DIESIS_SPOT_BOOK",
        "DIESIS_PERPS_BOOK",
        "DIESIS_MARGIN",
        "DIESIS_SETTLEMENT",
        "DIESIS_ERC20_FACTORY",
        "DIESIS_PERP_DEPLOY",
        "VRF",
        "STEALTH_REGISTRY",
        "STEALTH_ANNOUNCER",
        "SHIELDED_POOL",
        "PRIVACY_POOLS",
        "GROTH16_VERIFIER",
        "SECP256R1",
        "POSEIDON",
        "MULTICALL3",
        "PERMIT2",
    }
    actual = {n for n in dir(addresses) if not n.startswith("_")}
    assert expected == actual
