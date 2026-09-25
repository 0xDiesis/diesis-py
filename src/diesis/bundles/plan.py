"""Canonical bundle plan hashing and detached-consent signing.

The canonical encoder and plan hash reproduce ``canonical_bundle`` /
``plan_hash`` from ``crates/bundles/src/types.rs`` byte-for-byte, so a plan
hashed here matches the value the node recomputes at ``diesis_submitBundle``
admission. The cross-language fixed vector in ``docs/spec/bundles.md`` is pinned
by ``tests/test_bundles.py``.
"""

from __future__ import annotations

from typing import Any

from eth_account import Account
from eth_account.messages import encode_typed_data
from web3 import Web3

from .types import (
    DIESIS_BUNDLE_ESCROW,
    BundleManifestEntry,
    BundleMemberConsent,
    BundlePlan,
)

# Domain-separation tag prepended to the canonical bytes before hashing.
BUNDLE_PLAN_TAG = b"DIESIS_BUNDLE_PLAN_V1"

_CONSENT_TYPES = {
    "BundleMemberConsent": [
        {"name": "planHash", "type": "bytes32"},
        {"name": "memberIndex", "type": "uint16"},
        {"name": "transactionHash", "type": "bytes32"},
    ],
}


def _bytes_from_hex(field: str, value: str, width: int) -> bytes:
    if not isinstance(value, str) or not value.startswith("0x"):
        raise ValueError(f"{field} must be a 0x-prefixed hex string")
    try:
        raw = bytes.fromhex(value[2:])
    except ValueError as exc:
        raise ValueError(f"{field} must be valid hex") from exc
    if len(raw) != width:
        raise ValueError(f"{field} must be {width} bytes, got {len(raw)}")
    return raw


def _uint_be(field: str, value: int, width: int) -> bytes:
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(f"{field} must be an integer")
    if value < 0 or value >= 1 << (width * 8):
        raise ValueError(f"{field} must fit in uint{width * 8}")
    return value.to_bytes(width, "big")


def canonical_bundle(plan: BundlePlan) -> bytes:
    """Explicit, big-endian, length-prefixed canonical encoding of a plan.

    Fixed-width scalar fields in declaration order, then the member count, then
    each ordered ``(transaction_hash, gas_allowance)`` entry. The member index
    is implicit in ordering and is not encoded.
    """
    payment = plan.payment
    buf = bytearray()
    buf += _uint_be("chain_id", plan.chain_id, 8)
    buf += _uint_be("expiry", plan.expiry, 8)
    buf += _uint_be("flags", plan.flags, 2)
    buf += _bytes_from_hex("payer", payment.payer, 20)
    buf += _uint_be("maximum_builder_payment", payment.maximum_builder_payment, 32)
    buf += _uint_be("refund_gas_price", payment.refund_gas_price, 32)
    buf += _uint_be("maximum_refund", payment.maximum_refund, 32)
    buf += _uint_be("escrow_nonce", payment.escrow_nonce, 32)
    buf += _uint_be("member_count", len(plan.ordered_members), 4)
    for member in plan.ordered_members:
        buf += _bytes_from_hex("transaction_hash", member.transaction_hash, 32)
        buf += _uint_be("gas_allowance", member.gas_allowance, 8)
    return bytes(buf)


def plan_hash(plan: BundlePlan) -> str:
    """Domain-separated plan-hash commitment every member signs consent over."""
    digest = Web3.keccak(BUNDLE_PLAN_TAG + canonical_bundle(plan))
    return "0x" + digest.hex()


def consent_domain(chain_id: int, verifying_contract: str = DIESIS_BUNDLE_ESCROW) -> dict[str, Any]:
    """EIP-712 domain for a detached bundle-member consent."""
    return {
        "name": "Diesis Bundle",
        "version": "1",
        "chainId": chain_id,
        "verifyingContract": Web3.to_checksum_address(verifying_contract),
    }


def consent_typed_data(
    plan_hash_hex: str,
    member_index: int,
    transaction_hash: str,
    chain_id: int,
    verifying_contract: str = DIESIS_BUNDLE_ESCROW,
) -> dict[str, Any]:
    """Canonical EIP-712 typed data for ``BundleMemberConsent``."""
    return {
        "domain": consent_domain(chain_id, verifying_contract),
        "types": _CONSENT_TYPES,
        "primaryType": "BundleMemberConsent",
        "message": {
            "planHash": _bytes_from_hex("plan_hash", plan_hash_hex, 32),
            "memberIndex": member_index,
            "transactionHash": _bytes_from_hex("transaction_hash", transaction_hash, 32),
        },
    }


def sign_member_consent(
    private_key: str,
    plan: BundlePlan,
    member_index: int,
) -> BundleMemberConsent:
    """Sign the detached consent for one ordered member of a plan.

    Clients that call ``diesis_prepareBundle`` should prefer signing the
    returned ``member_digests`` directly; this helper reproduces the same
    EIP-712 digest locally for offline construction and verification.
    """
    if member_index < 0 or member_index >= len(plan.ordered_members):
        raise ValueError("member_index out of range for plan members")
    member: BundleManifestEntry = plan.ordered_members[member_index]
    ph = plan_hash(plan)
    typed = consent_typed_data(
        ph,
        member_index,
        member.transaction_hash,
        plan.chain_id,
    )
    signable = encode_typed_data(
        domain_data=typed["domain"],
        message_types=typed["types"],
        message_data=typed["message"],
    )
    signed = Account.sign_message(signable, private_key)
    return BundleMemberConsent(
        plan_hash=ph,
        member_index=member_index,
        transaction_hash=member.transaction_hash,
        signer=Account.from_key(private_key).address,
        signature="0x" + signed.signature.hex(),
    )
