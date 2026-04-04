"""Exchange RPC actions wrapping exchange_* methods."""

from __future__ import annotations

from typing import Any

from web3 import Web3
from web3.types import RPCEndpoint


class ExchangeActions:
    def __init__(self, w3: Web3) -> None:
        self._w3 = w3

    def _rpc(self, method: str, params: list[Any]) -> Any:
        response = self._w3.provider.make_request(RPCEndpoint(method), params)
        if "error" in response:
            raise RuntimeError(f"RPC error: {response['error']}")
        return response["result"]

    def get_order_book(self, market_id: str, depth: int | None = None) -> Any:
        params: dict[str, Any] = {"marketId": market_id}
        if depth is not None:
            params["depth"] = depth
        return self._rpc("exchange_getOrderBook", [params])

    def get_markets(self) -> Any:
        return self._rpc("exchange_getMarkets", [])

    def get_market(self, market_id: str) -> Any:
        return self._rpc("exchange_getMarket", [market_id])

    def get_account(self, address: str) -> Any:
        return self._rpc("exchange_getAccount", [address])

    def get_trades(self, market_id: str, limit: int | None = None) -> Any:
        params: dict[str, Any] = {"marketId": market_id}
        if limit is not None:
            params["limit"] = limit
        return self._rpc("exchange_getTrades", [params])

    def get_funding_rates(self, market_id: str) -> Any:
        return self._rpc("exchange_getFundingRates", [market_id])

    def estimate_fill(self, market_id: str, side: int, amount: int) -> Any:
        return self._rpc(
            "exchange_estimateFill",
            [{"marketId": market_id, "side": side, "amount": hex(amount)}],
        )
