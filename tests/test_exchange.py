from unittest.mock import MagicMock

from diesis.exchange.types import (
    FillEstimate, FundingRate, MarginType, MarketInfo, MarketStatus, MarketType,
    OrderBook, OrderType, PriceLevel, Side, Trade, TradingAccount,
)
from diesis.exchange.utils import market_id
from diesis.exchange.actions import ExchangeActions


def test_side_enum() -> None:
    assert Side.BUY == 0
    assert Side.SELL == 1


def test_order_type_enum() -> None:
    assert OrderType.LIMIT_GTC == 0
    assert OrderType.MARKET == 5
    assert OrderType.STOP_MARKET == 7


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
    try:
        pl.price = 200
        raise AssertionError("Should be frozen")
    except AttributeError:
        pass


def test_exchange_actions_get_order_book() -> None:
    mock_w3 = MagicMock()
    mock_w3.provider.make_request.return_value = {
        "result": {"bids": [], "asks": []}
    }
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
