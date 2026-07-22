"""Signed cancel-all and bounded stop-order helpers for the spot book.

Cancel-all lets a trader retire every resting order on a market with one signed
``CancelAllSpotIntent`` (EIP-712, spot-book domain). Stop orders reuse the
12-field ``OrderIntent`` with ``orderType`` set to ``STOP_LIMIT``/``STOP_MARKET``
and a ``triggerPrice``; a protected stop-limit must carry a nonzero ``price``.
Mirrors ``crates/exchange-wire/src/intent.rs`` and the spot-book precompile.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from eth_abi.abi import encode as abi_encode
from eth_account import Account
from eth_account.messages import encode_typed_data
from web3 import Web3

from ..addresses import DIESIS_SPOT_BOOK

TRIGGER_SPOT_STOPS_SIGNATURE = "triggerSpotStops(bytes32,uint16)"

# keccak256("StopOrderTriggered(bytes32,bytes32,address,uint256,uint256)").
STOP_ORDER_TRIGGERED_TOPIC = (
    "0x" + Web3.keccak(text="StopOrderTriggered(bytes32,bytes32,address,uint256,uint256)").hex()
)

_CANCEL_ALL_TYPES = {
    "CancelAllSpotIntent": [
        {"name": "trader", "type": "address"},
        {"name": "marketId", "type": "bytes32"},
        {"name": "expiry", "type": "uint64"},
        {"name": "nonce", "type": "uint256"},
    ],
}


@dataclass(frozen=True)
class CancelAllSpotIntent:
    """A trader's signed request to cancel every resting order on a market."""

    trader: str
    market_id: str
    expiry: int
    nonce: int


@dataclass(frozen=True)
class SignedCancelAllSpotIntent:
    """The cancel-all wire envelope: the intent plus its signature."""

    intent: CancelAllSpotIntent
    signature: str


def _bytes32(field: str, value: str) -> bytes:
    if not isinstance(value, str) or not value.startswith("0x") or len(value) != 66:
        raise ValueError(f"{field} must be a 0x-prefixed bytes32 hex string")
    return bytes.fromhex(value[2:])


def cancel_all_domain(chain_id: int = 1980, verifying_contract: str = DIESIS_SPOT_BOOK) -> dict[str, Any]:
    return {
        "name": "Diesis Exchange",
        "version": "2",
        "chainId": chain_id,
        "verifyingContract": Web3.to_checksum_address(verifying_contract),
    }


def cancel_all_typed_data(
    intent: CancelAllSpotIntent,
    chain_id: int = 1980,
    verifying_contract: str = DIESIS_SPOT_BOOK,
) -> dict[str, Any]:
    """Canonical EIP-712 typed data for a ``CancelAllSpotIntent``."""
    return {
        "domain": cancel_all_domain(chain_id, verifying_contract),
        "types": _CANCEL_ALL_TYPES,
        "primaryType": "CancelAllSpotIntent",
        "message": {
            "trader": Web3.to_checksum_address(intent.trader),
            "marketId": _bytes32("market_id", intent.market_id),
            "expiry": intent.expiry,
            "nonce": intent.nonce,
        },
    }


def sign_cancel_all_spot_intent(
    private_key: str,
    intent: CancelAllSpotIntent,
    chain_id: int = 1980,
    verifying_contract: str = DIESIS_SPOT_BOOK,
) -> SignedCancelAllSpotIntent:
    """Sign a cancel-all intent, returning the ``{intent, signature}`` envelope."""
    typed = cancel_all_typed_data(intent, chain_id, verifying_contract)
    signable = encode_typed_data(
        domain_data=typed["domain"],
        message_types=typed["types"],
        message_data=typed["message"],
    )
    signed = Account.sign_message(signable, private_key)
    return SignedCancelAllSpotIntent(intent=intent, signature="0x" + signed.signature.hex())


def encode_trigger_spot_stops(market_id: str, limit: int) -> str:
    """``triggerSpotStops(bytes32 marketId, uint16 limit)`` calldata (0x hex).

    Permissionless bounded continuation that triggers up to ``limit`` armed stop
    orders whose trigger price has been crossed on ``marketId``.
    """
    if limit < 0 or limit >= 1 << 16:
        raise ValueError("limit must fit in uint16")
    selector = bytes(Web3.keccak(text=TRIGGER_SPOT_STOPS_SIGNATURE)[:4])
    args = abi_encode(["bytes32", "uint16"], [_bytes32("market_id", market_id), limit])
    return "0x" + (selector + args).hex()
