"""Bundle V2 RPC actions wrapping the ``diesis_*Bundle`` methods.

Bundle V1 has been removed; these wrappers speak the V2 wire shapes only:
ordered plans with detached member consent, canonical plan hashing, and the
lifecycle/generation/payment fields on ``diesis_getBundleStatus``.
"""

from __future__ import annotations

from typing import Any, cast

from web3 import Web3

from .._rpc import _rpc
from .plan import plan_hash
from .types import (
    _LIFECYCLE_VALUES,
    _STATUS_VALUES,
    BundleFailure,
    BundleLifecycle,
    BundleMember,
    BundleMemberConsentV2,
    BundleMemberRole,
    BundleOrdering,
    BundlePaymentView,
    BundlePlanV2,
    BundleStatus,
    BundleStatusResult,
    PreparedBundle,
    SubmitBundleResult,
)
from .wire import consent_to_wire, plan_to_wire


def _rpc_dict(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise RuntimeError(f"Unexpected RPC result: {value!r}")
    return cast(dict[str, Any], value)


def _bundle_status(value: Any) -> BundleStatus:
    if value not in _STATUS_VALUES:
        raise RuntimeError(f"Unexpected bundle status: {value!r}")
    return cast(BundleStatus, value)


def _bundle_lifecycle(value: Any) -> BundleLifecycle:
    if value not in _LIFECYCLE_VALUES:
        raise RuntimeError(f"Unexpected bundle lifecycle: {value!r}")
    return cast(BundleLifecycle, value)


def _member_role(value: Any) -> BundleMemberRole:
    if value not in {"payment", "bundled"}:
        raise RuntimeError(f"Unexpected bundle member role: {value!r}")
    return cast(BundleMemberRole, value)


def _optional_str(value: Any) -> str | None:
    return value if isinstance(value, str) else None


def _optional_int(value: Any) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def _raw_to_wire(raw: str) -> list[int]:
    """Convert a 0x-hex raw transaction to the ``Vec<u8>`` wire form (int array)."""
    if not isinstance(raw, str) or not raw.startswith("0x"):
        raise ValueError("raw transaction must be a 0x-prefixed hex string")
    return list(bytes.fromhex(raw[2:]))


def _payment_view(value: Any) -> BundlePaymentView | None:
    if value is None:
        return None
    data = _rpc_dict(value)
    payer = data.get("payer")
    if not isinstance(payer, str):
        raise RuntimeError(f"Unexpected bundle payment payer: {payer!r}")
    return BundlePaymentView(
        payer=payer,
        maximum_builder_payment=str(data.get("maximumBuilderPayment")),
        refund_gas_price=str(data.get("refundGasPrice")),
        maximum_refund=str(data.get("maximumRefund")),
        escrow_nonce=str(data.get("escrowNonce")),
    )


def _bundle_failure(value: Any) -> BundleFailure | None:
    if value is None:
        return None
    data = _rpc_dict(value)
    reason = data.get("reason")
    if not isinstance(reason, str):
        raise RuntimeError(f"Unexpected bundle failure reason: {reason!r}")
    return BundleFailure(
        code=_optional_str(data.get("code")),
        reason=reason,
        failed_tx_hash=_optional_str(data.get("failedTxHash")),
        stage=_optional_str(data.get("stage")),
    )


def _bundle_ordering(value: Any) -> BundleOrdering | None:
    if value is None:
        return None
    data = _rpc_dict(value)
    return BundleOrdering(
        window=_optional_int(data.get("window")),
        batch_index=_optional_int(data.get("batchIndex")),
        position_in_batch=_optional_int(data.get("positionInBatch")),
    )


def _bundle_member(value: Any) -> BundleMember:
    data = _rpc_dict(value)
    index = data.get("index")
    if not isinstance(index, int) or isinstance(index, bool):
        raise RuntimeError(f"Unexpected bundle member index: {index!r}")
    return BundleMember(
        tx_hash=_optional_str(data.get("txHash")),
        index=index,
        role=_member_role(data.get("role")),
        status=_bundle_status(data.get("status")),
        failure_reason=_optional_str(data.get("failureReason")),
    )


def _prepared_bundle(value: Any) -> PreparedBundle:
    data = _rpc_dict(value)
    ph = data.get("planHash")
    version = data.get("version")
    digests = data.get("memberDigests")
    if not isinstance(ph, str) or not isinstance(version, int):
        raise RuntimeError(f"Unexpected prepare bundle result: {value!r}")
    if not isinstance(digests, list) or not all(isinstance(d, str) for d in digests):
        raise RuntimeError(f"Unexpected member digests: {digests!r}")
    return PreparedBundle(plan_hash=ph, version=version, member_digests=cast(list[str], digests))


def _submit_bundle_result(value: Any) -> SubmitBundleResult:
    data = _rpc_dict(value)
    ph = data.get("planHash")
    if not isinstance(ph, str):
        raise RuntimeError(f"Unexpected submit bundle result: {value!r}")
    return SubmitBundleResult(plan_hash=ph, status=_bundle_status(data.get("status")))


def _bundle_status_result(value: Any) -> BundleStatusResult:
    data = _rpc_dict(value)
    ph = data.get("planHash")
    bundle_hash = data.get("bundleHash")
    generation = data.get("generation")
    transaction_hashes = data.get("transactionHashes")
    members = data.get("members")
    if not isinstance(ph, str) or not isinstance(bundle_hash, str):
        raise RuntimeError(f"Unexpected bundle status result identity: {value!r}")
    if not isinstance(generation, int) or isinstance(generation, bool):
        raise RuntimeError(f"Unexpected bundle generation: {generation!r}")
    if not isinstance(transaction_hashes, list) or not all(isinstance(item, str) for item in transaction_hashes):
        raise RuntimeError(f"Unexpected bundle transaction hashes: {transaction_hashes!r}")
    if not isinstance(members, list):
        raise RuntimeError(f"Unexpected bundle members: {members!r}")
    return BundleStatusResult(
        plan_hash=ph,
        bundle_hash=bundle_hash,
        status=_bundle_status(data.get("status")),
        lifecycle=_bundle_lifecycle(data.get("lifecycle")),
        generation=generation,
        payment=_payment_view(data.get("payment")),
        submitted_at=_optional_int(data.get("submittedAt")),
        updated_at=_optional_int(data.get("updatedAt")),
        included_block_number=_optional_int(data.get("includedBlockNumber")),
        included_block_hash=_optional_str(data.get("includedBlockHash")),
        transaction_hashes=cast(list[str], transaction_hashes),
        members=[_bundle_member(member) for member in members],
        failure=_bundle_failure(data.get("failure")),
        ordering=_bundle_ordering(data.get("ordering")),
        error=_optional_str(data.get("error")),
    )


class BundleActions:
    """Client for the ``diesis_prepareBundle`` / ``submitBundle`` / status RPCs."""

    def __init__(self, w3: Web3) -> None:
        self._w3 = w3

    def prepare_bundle(self, plan: BundlePlanV2) -> PreparedBundle:
        """Bind an ordered plan and return its hash and per-member consent digests."""
        return _prepared_bundle(_rpc(self._w3, "diesis_prepareBundle", [{"plan": plan_to_wire(plan)}]))

    def submit_bundle(
        self,
        plan: BundlePlanV2,
        payment: str,
        members: list[tuple[str, BundleMemberConsentV2]],
    ) -> SubmitBundleResult:
        """Submit a fully-signed Bundle V2.

        ``payment`` is the 0x-hex raw reservation transaction; ``members`` pairs
        each ordered member's 0x-hex raw transaction with its detached consent.
        The plan hash is computed from ``plan`` and sent alongside the bundle.
        """
        ph = plan_hash(plan)
        bundle = {
            "plan": plan_to_wire(plan),
            "payment": _raw_to_wire(payment),
            "members": [
                {"rawTransaction": _raw_to_wire(raw), "consent": consent_to_wire(consent)} for raw, consent in members
            ],
        }
        return _submit_bundle_result(_rpc(self._w3, "diesis_submitBundle", [{"bundle": bundle, "planHash": ph}]))

    def get_bundle_status(self, plan_hash_hex: str) -> BundleStatusResult:
        return _bundle_status_result(_rpc(self._w3, "diesis_getBundleStatus", [{"planHash": plan_hash_hex}]))

    def send_stealth_bundle(
        self,
        plan: BundlePlanV2,
        funding: str,
        announcement: str,
        consent: BundleMemberConsentV2,
    ) -> SubmitBundleResult:
        """Submit a stealth (HALT_ON_INVALID single-member) bundle.

        The announcement signer attaches a detached ``BundleMemberConsentV2`` and
        the node assembles the ``HALT_ON_INVALID`` Bundle V2 committing exactly one
        ordered member (the announcement).
        """
        ph = plan_hash(plan)
        params = {
            "plan": plan_to_wire(plan),
            "planHash": ph,
            "funding": funding,
            "announcement": announcement,
            "consent": consent_to_wire(consent),
        }
        return _submit_bundle_result(_rpc(self._w3, "diesis_sendStealthBundle", [params]))
