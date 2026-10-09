"""Patronage RPC actions wrapping gas grant queries."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from web3 import Web3

from .._rpc import _rpc


@dataclass(frozen=True)
class GasGrant:
    grant_id: str
    balance: int
    total_contributed: int
    total_spent: int
    paused: bool


class PatronageActions:
    def __init__(self, w3: Web3) -> None:
        self._w3 = w3

    def get_grant(self, grant_id: str) -> Any:
        return _rpc(self._w3, "diesis_getGrant", [grant_id])
