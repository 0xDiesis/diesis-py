"""Bundle types and constants."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


class ExecutionFlags:
    STOP_ON_SUCCESS = 0x01
    TOLERATE_INVALID = 0x02
    HALT_ON_INVALID = 0x04
    PARTIAL_REFUND = 0x08


BUNDLE_ONLY_SENTINEL = "0x000000000000000000000000000000000A70B1C0"


@dataclass(frozen=True)
class PreparedBundle:
    plan_hash: str
    version: int


BundleStatus = Literal["pending", "included", "dropped", "unknown"]
BundleMemberRole = Literal["payment", "bundled"]


@dataclass(frozen=True)
class SubmitBundleResult:
    plan_hash: str
    status: BundleStatus


@dataclass(frozen=True)
class BundleMember:
    tx_hash: str | None
    index: int
    role: BundleMemberRole
    status: BundleStatus
    failure_reason: str | None


@dataclass(frozen=True)
class BundleFailure:
    code: str | None
    reason: str
    failed_tx_hash: str | None
    stage: str | None


@dataclass(frozen=True)
class BundleOrdering:
    window: int | None
    batch_index: int | None
    position_in_batch: int | None


@dataclass(frozen=True)
class BundleStatusResult:
    plan_hash: str
    bundle_hash: str
    status: BundleStatus
    submitted_at: int | None
    updated_at: int | None
    included_block_number: int | None
    included_block_hash: str | None
    transaction_hashes: list[str]
    members: list[BundleMember]
    failure: BundleFailure | None
    ordering: BundleOrdering | None
    error: str | None
