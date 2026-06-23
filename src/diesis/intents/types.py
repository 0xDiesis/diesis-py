"""Intent data types for EIP-712 signed orders."""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntFlag

ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"


class OrderFlags(IntFlag):
    """Order behavior flags mirrored from the core exchange wire format."""

    NONE = 0
    POST_ONLY = 1 << 0
    REDUCE_ONLY = 1 << 1
    IOC = 1 << 2
    FOK = 1 << 3


@dataclass(frozen=True)
class OrderIntent:
    """EIP-712 v2 order intent payload.

    Field names use Python snake_case while the signer serializes the canonical
    Solidity/EIP-712 names and field order used by the Rust and TypeScript SDKs.
    """

    trader: str
    market_id: str
    side: int
    order_type: int
    price: int
    amount: int
    nonce: int
    trigger_price: int = 0
    expiry: int = 0
    flags: int = int(OrderFlags.NONE)
    conductor: str = ZERO_ADDRESS
    conductor_fee_bps: int = 0
    max_conductor_fee: int = 0

    @property
    def reduce_only(self) -> bool:
        """Return whether the reduce-only order flag is set."""
        return bool(int(self.flags) & int(OrderFlags.REDUCE_ONLY))


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
