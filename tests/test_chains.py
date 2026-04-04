from diesis.chains import Chain, diesis, diesis_testnet


def test_mainnet_chain_id() -> None:
    assert diesis.id == 1980

def test_mainnet_name() -> None:
    assert diesis.name == "Diesis"

def test_mainnet_native_currency() -> None:
    assert diesis.native_currency.symbol == "DS"
    assert diesis.native_currency.decimals == 18

def test_mainnet_rpc() -> None:
    assert diesis.rpc_url == "https://rpc.diesis.xyz"

def test_testnet_chain_id() -> None:
    assert diesis_testnet.id == 19803

def test_testnet_is_testnet() -> None:
    assert diesis_testnet.testnet is True

def test_mainnet_is_not_testnet() -> None:
    assert diesis.testnet is False

def test_chain_is_frozen() -> None:
    import dataclasses
    assert dataclasses.is_dataclass(diesis)
    try:
        diesis.id = 999
        raise AssertionError("Should be frozen")
    except dataclasses.FrozenInstanceError:
        pass
