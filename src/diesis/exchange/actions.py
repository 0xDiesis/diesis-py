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

    # ── Cycle A2.1: operator-deployed perp markets ───────────────────────────

    def deploy_perp(self, params: dict[str, Any]) -> Any:
        """Submit an `IDiesisPerpDeploy.activate` call.

        ``params`` mirrors the TS SDK shape:
        ``{slotId, sourceList, metadata, sigs}``.
        """
        return self._rpc("exchange_deployPerp", [params])

    def get_market_deployment_state(self, market_id: str) -> Any:
        """Read the deployment state for ``market_id`` (Cycle A2.1)."""
        return self._rpc("exchange_getMarketDeploymentState", [market_id])

    def get_operator_balance(self, operator: str) -> Any:
        """Read the operator-fee-router balance for ``operator``."""
        return self._rpc("exchange_getOperatorBalance", [operator])

    def propose_metadata_update(self, params: dict[str, Any]) -> Any:
        """Propose a market-metadata update (24h timelock)."""
        return self._rpc("exchange_proposeMetadataUpdate", [params])
