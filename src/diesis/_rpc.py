"""Shared JSON-RPC request handling for SDK actions."""

from __future__ import annotations

from typing import Any

from web3 import Web3
from web3.types import RPCEndpoint

from .rpc_errors import RpcError


def _rpc(w3: Web3, method: str, params: list[Any]) -> Any:
    response = w3.provider.make_request(RPCEndpoint(method), params)
    if "error" in response:
        raise RpcError(response["error"])
    return response["result"]
