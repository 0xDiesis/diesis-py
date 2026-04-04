"""Patronage RPC actions wrapping diesis_getPatronFund."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from web3 import Web3
from web3.types import RPCEndpoint


@dataclass(frozen=True)
class PatronFund:
    balance: int
    patron: str
    fund_type: int


class PatronageActions:
    def __init__(self, w3: Web3) -> None:
        self._w3 = w3

    def _rpc(self, method: str, params: list[Any]) -> Any:
        response = self._w3.provider.make_request(RPCEndpoint(method), params)
        if "error" in response:
            raise RuntimeError(f"RPC error: {response['error']}")
        return response["result"]

    def get_patron_fund(self, fund_key: str) -> Any:
        return self._rpc("diesis_getPatronFund", [fund_key])
