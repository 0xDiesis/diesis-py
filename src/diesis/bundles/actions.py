"""Bundle RPC actions wrapping diesis_*Bundle methods."""
from __future__ import annotations
from typing import Any
from web3 import Web3

class BundleActions:
    def __init__(self, w3: Web3) -> None:
        self._w3 = w3

    def _rpc(self, method: str, params: list[Any]) -> Any:
        response = self._w3.provider.make_request(method, params)
        if "error" in response:
            raise RuntimeError(f"RPC error: {response['error']}")
        return response["result"]

    def prepare_bundle(self, payment: str, bundle: list[str], flags: int) -> Any:
        return self._rpc("diesis_prepareBundle", [{"payment": payment, "bundle": bundle, "flags": flags}])

    def submit_bundle(self, plan_hash: str, payment: str, bundle: list[str], flags: int) -> Any:
        return self._rpc("diesis_submitBundle", [{"planHash": plan_hash, "payment": payment, "bundle": bundle, "flags": flags}])

    def get_bundle_status(self, plan_hash: str) -> Any:
        return self._rpc("diesis_getBundleStatus", [plan_hash])
