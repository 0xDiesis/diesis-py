from unittest.mock import MagicMock

import pytest

from diesis.exchange.actions import ExchangeActions, erc20_symbol
from diesis.exchange.types import (
    OrderType,
    PriceLevel,
    Side,
)
from diesis.exchange.utils import market_id


def test_side_enum() -> None:
    assert int(Side.BUY) == 0
    assert int(Side.SELL) == 1


def test_order_type_enum() -> None:
    assert int(OrderType.LIMIT) == 0
    assert int(OrderType.MARKET) == 1
    assert int(OrderType.STOP_LIMIT) == 2
    assert int(OrderType.STOP_MARKET) == 3


def test_market_id_deterministic() -> None:
    base = "0x0000000000000000000000000000000000000001"
    quote = "0x0000000000000000000000000000000000000002"
    mid = market_id(base, quote)
    assert mid == market_id(base, quote)
    assert mid.startswith("0x")
    assert len(mid) == 66


def test_market_id_different_for_spot_vs_perp() -> None:
    base = "0x0000000000000000000000000000000000000001"
    quote = "0x0000000000000000000000000000000000000002"
    spot = market_id(base, quote, 0)
    perp = market_id(base, quote, 1)
    assert spot != perp


def test_price_level_frozen() -> None:
    pl = PriceLevel(price=100, amount=50, orders=3)
    assert pl.price == 100
    with pytest.raises(AttributeError):
        pl.price = 200  # type: ignore[misc]


def test_exchange_actions_get_order_book() -> None:
    mock_w3 = MagicMock()
    mock_w3.provider.make_request.return_value = {"result": {"bids": [], "asks": []}}
    actions = ExchangeActions(mock_w3)
    actions.get_order_book("0x" + "ab" * 32)
    call_args = mock_w3.provider.make_request.call_args
    assert call_args[0][0] == "exchange_getOrderBook"


def test_exchange_actions_get_markets() -> None:
    mock_w3 = MagicMock()
    mock_w3.provider.make_request.return_value = {"result": []}
    actions = ExchangeActions(mock_w3)
    actions.get_markets()
    call_args = mock_w3.provider.make_request.call_args
    assert call_args[0][0] == "exchange_getMarkets"


def test_exchange_actions_estimate_fill() -> None:
    mock_w3 = MagicMock()
    mock_w3.provider.make_request.return_value = {
        "result": {"avgPrice": "0x64", "totalCost": "0xc8", "fills": 3, "slippageBps": 10}
    }
    actions = ExchangeActions(mock_w3)
    actions.estimate_fill("0x" + "ab" * 32, Side.BUY, 1000)
    call_args = mock_w3.provider.make_request.call_args
    assert call_args[0][0] == "exchange_estimateFill"


# ── Cycle A2.1: operator-deployed perp markets RPC bindings ──────────────────


def test_exchange_actions_deploy_perp() -> None:
    mock_w3 = MagicMock()
    mock_w3.provider.make_request.return_value = {"result": {"marketId": "0x" + "00" * 32}}
    actions = ExchangeActions(mock_w3)
    actions.deploy_perp(
        {
            "slotId": "0x" + "11" * 32,
            "sourceList": {"sources": []},
            "metadata": {"maxLeverage": 10, "backstopTopupBps": 500, "marginTiers": []},
            "sigs": [],
        }
    )
    call_args = mock_w3.provider.make_request.call_args
    assert call_args[0][0] == "exchange_deployPerp"


def test_exchange_actions_get_market_deployment_state() -> None:
    mock_w3 = MagicMock()
    mock_w3.provider.make_request.return_value = {"result": {"tag": "live"}}
    actions = ExchangeActions(mock_w3)
    actions.get_market_deployment_state("0x" + "ab" * 32)
    call_args = mock_w3.provider.make_request.call_args
    assert call_args[0][0] == "exchange_getMarketDeploymentState"


def test_exchange_actions_get_operator_balance() -> None:
    mock_w3 = MagicMock()
    mock_w3.provider.make_request.return_value = {"result": "0x0"}
    actions = ExchangeActions(mock_w3)
    actions.get_operator_balance("0x" + "00" * 20)
    call_args = mock_w3.provider.make_request.call_args
    assert call_args[0][0] == "exchange_getOperatorBalance"


def test_exchange_actions_propose_metadata_update() -> None:
    mock_w3 = MagicMock()
    mock_w3.provider.make_request.return_value = {"result": {"unlockBlock": "0x0"}}
    actions = ExchangeActions(mock_w3)
    actions.propose_metadata_update(
        {
            "marketId": "0x" + "ab" * 32,
            "newMetadata": {"maxLeverage": 5, "backstopTopupBps": 500, "marginTiers": []},
            "sigs": [],
        }
    )
    call_args = mock_w3.provider.make_request.call_args
    assert call_args[0][0] == "exchange_proposeMetadataUpdate"


# ── A2.1.1: ERC-20 factory precompile EVM dispatch ──────────────────────────


def test_erc20_symbol_normalizes_to_bytes11() -> None:
    assert erc20_symbol("DIE") == b"DIE" + b"\x00" * 8
    assert erc20_symbol(b"DIESIS") == b"DIESIS" + b"\x00" * 5


def test_erc20_symbol_rejects_invalid_input() -> None:
    with pytest.raises(ValueError):
        erc20_symbol("D")
    with pytest.raises(ValueError):
        erc20_symbol("DIESIS-TOKEN")


def test_exchange_actions_predict_erc20_address() -> None:
    mock_w3 = MagicMock()
    mock_contract = MagicMock()
    mock_contract.functions.predictAddress.return_value.call.return_value = "0x" + "12" * 20
    mock_w3.eth.contract.return_value = mock_contract
    actions = ExchangeActions(mock_w3)

    result = actions.predict_erc20_address("0x" + "34" * 20, "DIE")

    assert result == "0x" + "12" * 20
    mock_contract.functions.predictAddress.assert_called_once()


def test_exchange_actions_deploy_erc20() -> None:
    mock_w3 = MagicMock()
    mock_contract = MagicMock()
    mock_contract.functions.deploy.return_value.transact.return_value = b"\xab" * 32
    mock_w3.eth.contract.return_value = mock_contract
    actions = ExchangeActions(mock_w3)

    result = actions.deploy_erc20(
        symbol="DIE",
        name="Diesis",
        initial_supply=1,
        deployer="0x" + "34" * 20,
        from_="0x" + "56" * 20,
    )

    assert result == b"\xab" * 32
    mock_contract.functions.deploy.assert_called_once()
