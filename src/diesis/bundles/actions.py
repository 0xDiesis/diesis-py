"""Bundle RPC actions wrapping diesis_*Bundle methods."""

from __future__ import annotations

from typing import Any, cast

from web3 import Web3
from web3.types import RPCEndpoint

from .types import (
    BundleFailure,
    BundleMember,
    BundleMemberRole,
    BundleOrdering,
    BundleStatus,
    BundleStatusResult,
    PreparedBundle,
    SubmitBundleResult,
)


def _rpc_dict(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise RuntimeError(f"Unexpected RPC result: {value!r}")
    return cast(dict[str, Any], value)


def _bundle_status(value: Any) -> BundleStatus:
    if value not in {"pending", "included", "dropped", "unknown"}:
        raise RuntimeError(f"Unexpected bundle status: {value!r}")
    return cast(BundleStatus, value)


def _member_role(value: Any) -> BundleMemberRole:
    if value not in {"payment", "bundled"}:
        raise RuntimeError(f"Unexpected bundle member role: {value!r}")
    return cast(BundleMemberRole, value)


def _optional_str(value: Any) -> str | None:
    return value if isinstance(value, str) else None


def _optional_int(value: Any) -> int | None:
    return value if isinstance(value, int) else None


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
    if not isinstance(index, int):
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
    plan_hash = data.get("planHash")
    version = data.get("version")
    if not isinstance(plan_hash, str) or not isinstance(version, int):
        raise RuntimeError(f"Unexpected prepare bundle result: {value!r}")
    return PreparedBundle(plan_hash=plan_hash, version=version)


def _submit_bundle_result(value: Any) -> SubmitBundleResult:
    data = _rpc_dict(value)
    plan_hash = data.get("planHash")
    if not isinstance(plan_hash, str):
        raise RuntimeError(f"Unexpected submit bundle result: {value!r}")
    return SubmitBundleResult(plan_hash=plan_hash, status=_bundle_status(data.get("status")))


def _bundle_status_result(value: Any) -> BundleStatusResult:
    data = _rpc_dict(value)
    plan_hash = data.get("planHash")
    bundle_hash = data.get("bundleHash")
    transaction_hashes = data.get("transactionHashes")
    members = data.get("members")
    if not isinstance(plan_hash, str) or not isinstance(bundle_hash, str):
        raise RuntimeError(f"Unexpected bundle status result identity: {value!r}")
    if not isinstance(transaction_hashes, list) or not all(isinstance(item, str) for item in transaction_hashes):
        raise RuntimeError(f"Unexpected bundle transaction hashes: {transaction_hashes!r}")
    if not isinstance(members, list):
        raise RuntimeError(f"Unexpected bundle members: {members!r}")
    return BundleStatusResult(
        plan_hash=plan_hash,
        bundle_hash=bundle_hash,
        status=_bundle_status(data.get("status")),
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
    def __init__(self, w3: Web3) -> None:
        self._w3 = w3

    def _rpc(self, method: str, params: list[Any]) -> Any:
        response = self._w3.provider.make_request(RPCEndpoint(method), params)
        if "error" in response:
            raise RuntimeError(f"RPC error: {response['error']}")
        return response["result"]

    def prepare_bundle(self, payment: str, bundle: list[str], flags: int) -> PreparedBundle:
        return _prepared_bundle(
            self._rpc(
                "diesis_prepareBundle",
                [{"payment": payment, "bundle": bundle, "flags": flags}],
            )
        )

    def submit_bundle(self, plan_hash: str, payment: str, bundle: list[str], flags: int) -> SubmitBundleResult:
        return _submit_bundle_result(
            self._rpc(
                "diesis_submitBundle",
                [{"planHash": plan_hash, "payment": payment, "bundle": bundle, "flags": flags}],
            )
        )

    def get_bundle_status(self, plan_hash: str) -> BundleStatusResult:
        return _bundle_status_result(self._rpc("diesis_getBundleStatus", [{"planHash": plan_hash}]))
