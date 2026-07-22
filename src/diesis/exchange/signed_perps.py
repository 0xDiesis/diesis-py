"""Sponsored, signed bounded V2 perpetual action envelopes.

Mirrors ``SignedPerpActionsV2`` in ``crates/exchange-wire/src/intent.rs``. A
trader signs ``{trader, nonce, expiry, actionsHash}`` as EIP-712 typed data under
the perps-book domain; the relayer submits it via ``submitSignedPerpActionsV2(bytes)``
without ever becoming the trading principal. ``actionsHash`` commits to the
canonical ``ExchangeActionBatchV2`` bytes so any mutation invalidates the
signature.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from eth_account import Account
from eth_account.messages import encode_typed_data
from web3 import Web3

from ..addresses import DIESIS_PERPS_BOOK

SUBMIT_SIGNED_PERP_ACTIONS_V2_SIGNATURE = "submitSignedPerpActionsV2(bytes)"

_SIGNED_PERP_ACTIONS_V2_TYPES = {
    "SignedPerpActionsV2": [
        {"name": "trader", "type": "address"},
        {"name": "nonce", "type": "uint256"},
        {"name": "expiry", "type": "uint64"},
        {"name": "actionsHash", "type": "bytes32"},
    ],
}


@dataclass(frozen=True)
class SignedPerpActionsV2:
    """A signed perpetual action envelope and its recovered signer."""

    trader: str
    nonce: int
    expiry: int
    actions_hash: str
    actions: str
    signature: str
    signer: str


def _bytes32(field: str, value: str) -> bytes:
    if not isinstance(value, str) or not value.startswith("0x") or len(value) != 66:
        raise ValueError(f"{field} must be a 0x-prefixed bytes32 hex string")
    return bytes.fromhex(value[2:])


def actions_hash(actions: str) -> str:
    """keccak256 over the canonical action bytes (``0x``-hex in, ``0x``-hex out)."""
    if not isinstance(actions, str) or not actions.startswith("0x"):
        raise ValueError("actions must be a 0x-prefixed hex string")
    return "0x" + Web3.keccak(bytes.fromhex(actions[2:])).hex()


def perps_domain(chain_id: int = 1980, verifying_contract: str = DIESIS_PERPS_BOOK) -> dict[str, Any]:
    """EIP-712 domain for perps-book intents (verifying contract = perps book)."""
    return {
        "name": "Diesis Exchange",
        "version": "2",
        "chainId": chain_id,
        "verifyingContract": Web3.to_checksum_address(verifying_contract),
    }


def signed_perp_actions_typed_data(
    trader: str,
    nonce: int,
    expiry: int,
    actions_hash_hex: str,
    chain_id: int = 1980,
    verifying_contract: str = DIESIS_PERPS_BOOK,
) -> dict[str, Any]:
    """Canonical EIP-712 typed data for a ``SignedPerpActionsV2`` envelope."""
    return {
        "domain": perps_domain(chain_id, verifying_contract),
        "types": _SIGNED_PERP_ACTIONS_V2_TYPES,
        "primaryType": "SignedPerpActionsV2",
        "message": {
            "trader": Web3.to_checksum_address(trader),
            "nonce": nonce,
            "expiry": expiry,
            "actionsHash": _bytes32("actions_hash", actions_hash_hex),
        },
    }


def sign_perp_actions(
    private_key: str,
    trader: str,
    nonce: int,
    expiry: int,
    actions: str,
    chain_id: int = 1980,
    verifying_contract: str = DIESIS_PERPS_BOOK,
) -> SignedPerpActionsV2:
    """Sign a bounded V2 perpetual action batch for ``trader``.

    ``actions`` is the canonical ``ExchangeActionBatchV2`` byte payload as 0x-hex.
    The commitment ``actionsHash = keccak256(actions)`` is computed and signed.
    """
    ah = actions_hash(actions)
    typed = signed_perp_actions_typed_data(trader, nonce, expiry, ah, chain_id, verifying_contract)
    signable = encode_typed_data(
        domain_data=typed["domain"],
        message_types=typed["types"],
        message_data=typed["message"],
    )
    signed = Account.sign_message(signable, private_key)
    return SignedPerpActionsV2(
        trader=Web3.to_checksum_address(trader),
        nonce=nonce,
        expiry=expiry,
        actions_hash=ah,
        actions=actions,
        signature="0x" + signed.signature.hex(),
        signer=Account.from_key(private_key).address,
    )
