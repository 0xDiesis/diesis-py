"""Exchange data types mirroring the TypeScript SDK."""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum


class Side(IntEnum):
    BUY = 0
    SELL = 1


class OrderType(IntEnum):
    LIMIT_GTC = 0
    LIMIT_GTD = 1
    LIMIT_IOC = 2
    LIMIT_FOK = 3
    LIMIT_POST_ONLY = 4
    MARKET = 5
    STOP_LIMIT = 6
    STOP_MARKET = 7


class MarginType(IntEnum):
    CROSS = 0
    ISOLATED = 1
    UNIFIED = 2


class MarketType(IntEnum):
    SPOT = 0
    PERP = 1


class MarketStatus(IntEnum):
    CREATED = 0
    ACTIVE = 1
    PAUSED = 2
    DELISTED = 3


@dataclass(frozen=True)
class PriceLevel:
    price: int
    amount: int
    orders: int


@dataclass(frozen=True)
class OrderBook:
    bids: list[PriceLevel]
    asks: list[PriceLevel]


@dataclass(frozen=True)
class MarketInfo:
    market_id: str
    base_token: str
    quote_token: str
    market_type: MarketType
    status: MarketStatus
    tick_size: int
    lot_size: int


@dataclass(frozen=True)
class TradingAccount:
    available: int
    locked_in_orders: int
    locked_in_margin: int


@dataclass(frozen=True)
class Position:
    market_id: str
    owner: str
    side: Side
    size: int
    entry_price: int
    margin_type: MarginType
    isolated_margin: int
    realized_pnl: int
    last_funding_index: int


@dataclass(frozen=True)
class Trade:
    market_id: str
    order_id: str
    trader: str
    fill_price: int
    fill_amount: int
    is_maker: bool
    block_number: int


@dataclass(frozen=True)
class FundingRate:
    market_id: str
    rate: int
    timestamp: int


@dataclass(frozen=True)
class FillEstimate:
    avg_price: int
    total_cost: int
    fills: int
    slippage_bps: int
