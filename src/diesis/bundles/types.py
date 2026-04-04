"""Bundle types and constants."""
from __future__ import annotations
from dataclasses import dataclass

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

@dataclass(frozen=True)
class BundleResult:
    plan_hash: str
    status: str
