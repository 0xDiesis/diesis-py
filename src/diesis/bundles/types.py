"""Bundle V2 types and constants.

Mirrors ``crates/bundles/src/types.rs`` and ``docs/spec/bundles.md``. Bundle V1
(access-list consent, payment/flags-only plan hash) has been removed; the V2
types below are the only accepted shapes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


class ExecutionFlags:
    """``u16`` bundle execution bitflags (see the spec precedence table)."""

    STOP_ON_SUCCESS = 0x01
    TOLERATE_INVALID = 0x02
    HALT_ON_INVALID = 0x04
    PARTIAL_REFUND = 0x08


# Escrow precompile reserved on every chain spec so all languages derive an
# identical bundle EIP-712 domain and reservation target.
DIESIS_BUNDLE_ESCROW = "0xD1E515000000000000000000000000000000bE5c"


@dataclass(frozen=True)
class BundlePaymentTerms:
    """Committed builder-payment and skipped-work refund terms."""

    payer: str
    maximum_builder_payment: int
    refund_gas_price: int
    maximum_refund: int
    escrow_nonce: int


@dataclass(frozen=True)
class BundleManifestEntry:
    """One ordered manifest member: a transaction hash and its gas allowance."""

    transaction_hash: str
    gas_allowance: int


@dataclass(frozen=True)
class BundlePlanV2:
    """The ordered plan every member's detached consent commits to."""

    chain_id: int
    expiry: int
    flags: int
    payment: BundlePaymentTerms
    ordered_members: list[BundleManifestEntry] = field(default_factory=list)


@dataclass(frozen=True)
class BundleMemberConsentV2:
    """A member's detached EIP-712 consent over the plan and its own slot."""

    plan_hash: str
    member_index: int
    transaction_hash: str
    signer: str
    signature: str


# Coarse admission/inclusion status (`BundleStatus`, lowercase serde).
BundleStatus = Literal[
    "pending",
    "included",
    "payment_failed",
    "payment_consumed",
    "dropped",
    "unknown",
]

# Canonical per-node lifecycle string returned by ``diesis_getBundleStatus``.
BundleLifecycle = Literal[
    "admitted",
    "disseminating",
    "ready",
    "proposed",
    "canonical",
    "reverted",
    "expired",
    "dropped",
    "unknown",
]

BundleMemberRole = Literal["payment", "bundled"]

_STATUS_VALUES: frozenset[str] = frozenset(
    ("pending", "included", "payment_failed", "payment_consumed", "dropped", "unknown")
)

_LIFECYCLE_VALUES: frozenset[str] = frozenset(
    (
        "admitted",
        "disseminating",
        "ready",
        "proposed",
        "canonical",
        "reverted",
        "expired",
        "dropped",
        "unknown",
    )
)


@dataclass(frozen=True)
class PreparedBundle:
    """Result of ``diesis_prepareBundle``.

    ``member_digests`` are the EIP-712 signing digests a client signs directly
    (low-S, ``v`` in ``{27, 28}``) rather than re-deriving the consent digest.
    """

    plan_hash: str
    version: int
    member_digests: list[str]


@dataclass(frozen=True)
class SubmitBundleResult:
    plan_hash: str
    status: BundleStatus


@dataclass(frozen=True)
class BundlePaymentView:
    """Committed escrow terms echoed on the status response (U256 as hex)."""

    payer: str
    maximum_builder_payment: str
    refund_gas_price: str
    maximum_refund: str
    escrow_nonce: str


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
    lifecycle: BundleLifecycle
    generation: int
    payment: BundlePaymentView | None
    submitted_at: int | None
    updated_at: int | None
    included_block_number: int | None
    included_block_hash: str | None
    transaction_hashes: list[str]
    members: list[BundleMember]
    failure: BundleFailure | None
    ordering: BundleOrdering | None
    error: str | None
