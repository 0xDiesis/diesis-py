"""Intent data types for EIP-712 signed orders."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class OrderIntent:
    market_id: str
    side: int
    price: int
    amount: int
    order_type: int
    nonce: int
    expiry: int
    reduce_only: bool


@dataclass(frozen=True)
class SignedOrderIntent:
    intent: OrderIntent
    signature: str
    signer: str


@dataclass(frozen=True)
class TradingKeyAuthorization:
    trading_key: str
    expiry: int
    max_notional: int
    markets: list[str]
    can_withdraw: bool
