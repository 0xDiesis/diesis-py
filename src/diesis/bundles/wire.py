"""Wire (JSON-RPC) serialization for Bundle V2 plans and consent.

The node deserializes ``BundlePlanV2`` with ``serde(rename_all = "camelCase")``.
Two encoding caveats are reproduced here:

* ``flags`` serialize as a string of set ``ExecutionFlags`` names joined by
  `` | `` (the ``bitflags`` serde form), e.g. ``"HALT_ON_INVALID | PARTIAL_REFUND"``.
* ``U256`` payment fields serialize as ruint quantity hex strings (``"0x..."``).
"""

from __future__ import annotations

from typing import Any

from web3 import Web3

from .types import (
    BundleManifestEntry,
    BundleMemberConsentV2,
    BundlePaymentTerms,
    BundlePlanV2,
    ExecutionFlags,
)

# Declaration order, matching the Rust `bitflags!` definition.
_FLAG_NAMES: list[tuple[str, int]] = [
    ("STOP_ON_SUCCESS", ExecutionFlags.STOP_ON_SUCCESS),
    ("TOLERATE_INVALID", ExecutionFlags.TOLERATE_INVALID),
    ("HALT_ON_INVALID", ExecutionFlags.HALT_ON_INVALID),
    ("PARTIAL_REFUND", ExecutionFlags.PARTIAL_REFUND),
]

_KNOWN_FLAG_BITS = 0x0F


def flags_to_wire(flags: int) -> str:
    """Encode ``ExecutionFlags`` bits as the ``bitflags`` serde name string."""
    if flags & ~_KNOWN_FLAG_BITS:
        raise ValueError(f"flags contains unsupported bits: {flags:#06x}")
    names = [name for name, bit in _FLAG_NAMES if flags & bit]
    return " | ".join(names)


def flags_from_wire(value: str) -> int:
    """Decode a ``bitflags`` serde name string back to raw bits."""
    if not isinstance(value, str):
        raise ValueError("flags wire value must be a string")
    lookup = {name: bit for name, bit in _FLAG_NAMES}
    bits = 0
    for token in (t.strip() for t in value.split("|")):
        if not token:
            continue
        if token not in lookup:
            raise ValueError(f"unknown ExecutionFlags name: {token!r}")
        bits |= lookup[token]
    return bits


def _u256_hex(value: int) -> str:
    if value < 0 or value >= 1 << 256:
        raise ValueError("value must fit in uint256")
    return hex(value)


def payment_to_wire(payment: BundlePaymentTerms) -> dict[str, Any]:
    return {
        "payer": Web3.to_checksum_address(payment.payer),
        "maximumBuilderPayment": _u256_hex(payment.maximum_builder_payment),
        "refundGasPrice": _u256_hex(payment.refund_gas_price),
        "maximumRefund": _u256_hex(payment.maximum_refund),
        "escrowNonce": _u256_hex(payment.escrow_nonce),
    }


def member_to_wire(member: BundleManifestEntry) -> dict[str, Any]:
    return {
        "transactionHash": member.transaction_hash,
        "gasAllowance": member.gas_allowance,
    }


def plan_to_wire(plan: BundlePlanV2) -> dict[str, Any]:
    """Serialize a ``BundlePlanV2`` to its camelCase JSON-RPC form."""
    return {
        "chainId": plan.chain_id,
        "expiry": plan.expiry,
        "flags": flags_to_wire(plan.flags),
        "payment": payment_to_wire(plan.payment),
        "orderedMembers": [member_to_wire(m) for m in plan.ordered_members],
    }


def consent_to_wire(consent: BundleMemberConsentV2) -> dict[str, Any]:
    return {
        "planHash": consent.plan_hash,
        "memberIndex": consent.member_index,
        "transactionHash": consent.transaction_hash,
        "signer": Web3.to_checksum_address(consent.signer),
        "signature": consent.signature,
    }
