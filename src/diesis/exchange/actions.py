"""Exchange RPC actions wrapping exchange_* methods."""

from __future__ import annotations

from typing import Any, cast

from web3 import Web3
from web3.contract import Contract
from web3.types import TxParams

from .._rpc import _rpc
from ..abi.generated.IDiesisErc20Factory import IDIESISERC20FACTORY_ABI
from ..addresses import DIESIS_ERC20_FACTORY

ERC20_FACTORY_ABI: list[dict[str, Any]] = [
    next(entry for entry in IDIESISERC20FACTORY_ABI if entry["type"] == "function" and entry["name"] == name)
    for name in (
        "deploy",
        "predictAddress",
        "templateBytecodeHash",
        "proposeTemplateUpdate",
        "executeTemplateUpdate",
    )
]


def erc20_symbol(symbol: str | bytes) -> bytes:
    """Return the factory's bytes11 symbol encoding."""
    raw = symbol.encode("ascii") if isinstance(symbol, str) else symbol
    if len(raw) < 2 or len(raw) > 11 or not raw.isalnum() or any(byte > 0x7F for byte in raw):
        raise ValueError("ERC-20 factory symbol must be 2-11 ASCII alphanumeric characters")
    return raw.ljust(11, b"\x00")


def _tx_params(params: dict[str, Any]) -> TxParams:
    if "from_" in params:
        params = {**params, "from": params["from_"]}
        del params["from_"]
    return cast(TxParams, params)


class ExchangeActions:
    def __init__(self, w3: Web3) -> None:
        self._w3 = w3
        self._erc20_factory: Contract = w3.eth.contract(
            address=Web3.to_checksum_address(DIESIS_ERC20_FACTORY),
            abi=ERC20_FACTORY_ABI,
        )

    def get_order_book(self, market_id: str, depth: int | None = None) -> Any:
        params: dict[str, Any] = {"marketId": market_id}
        if depth is not None:
            params["depth"] = depth
        return _rpc(self._w3, "exchange_getOrderBook", [params])

    def get_markets(self) -> Any:
        return _rpc(self._w3, "exchange_getMarkets", [])

    def get_market(self, market_id: str) -> Any:
        return _rpc(self._w3, "exchange_getMarket", [market_id])

    def get_account(self, address: str) -> Any:
        return _rpc(self._w3, "exchange_getAccount", [address])

    def get_trades(self, market_id: str, limit: int | None = None) -> Any:
        params: dict[str, Any] = {"marketId": market_id}
        if limit is not None:
            params["limit"] = limit
        return _rpc(self._w3, "exchange_getTrades", [params])

    def get_funding_rates(self, market_id: str) -> Any:
        return _rpc(self._w3, "exchange_getFundingRates", [market_id])

    def estimate_fill(self, market_id: str, side: int, amount: int) -> Any:
        return _rpc(
            self._w3,
            "exchange_estimateFill",
            [{"marketId": market_id, "side": side, "amount": hex(amount)}],
        )

    # ── Cycle A2.1: operator-deployed perp markets ───────────────────────────

    def deploy_perp(self, params: dict[str, Any]) -> Any:
        """Submit an `IDiesisPerpDeploy.activate` call.

        ``params`` mirrors the TS SDK shape:
        ``{slotId, sourceList, metadata, sigs}``.
        """
        return _rpc(self._w3, "exchange_deployPerp", [params])

    def get_market_deployment_state(self, market_id: str) -> Any:
        """Read the deployment state for ``market_id`` (Cycle A2.1)."""
        return _rpc(self._w3, "exchange_getMarketDeploymentState", [market_id])

    def get_operator_balance(self, operator: str) -> Any:
        """Read the operator-fee-router balance for ``operator``."""
        return _rpc(self._w3, "exchange_getOperatorBalance", [operator])

    def propose_metadata_update(self, params: dict[str, Any]) -> Any:
        """Propose a market-metadata update (24h timelock)."""
        return _rpc(self._w3, "exchange_proposeMetadataUpdate", [params])

    # ── A2.1.1: ERC-20 factory precompile EVM dispatch ──────────────────────

    def predict_erc20_address(self, deployer: str, symbol: str | bytes) -> str:
        """Predict the deterministic factory token address for ``deployer`` and ``symbol``."""
        return str(
            self._erc20_factory.functions.predictAddress(
                Web3.to_checksum_address(deployer),
                erc20_symbol(symbol),
            ).call()
        )

    def get_erc20_template_bytecode_hash(self) -> Any:
        """Read the currently pinned ERC-20 template runtime bytecode hash."""
        return self._erc20_factory.functions.templateBytecodeHash().call()

    def deploy_erc20(
        self,
        *,
        symbol: str | bytes,
        name: str,
        initial_supply: int,
        deployer: str,
        **tx_params: Any,
    ) -> Any:
        """Dispatch ``IDiesisErc20Factory.deploy`` as an EVM transaction."""
        params = (
            erc20_symbol(symbol),
            name,
            initial_supply,
            Web3.to_checksum_address(deployer),
        )
        return self._erc20_factory.functions.deploy(params).transact(_tx_params(tx_params))

    def propose_erc20_template_update(self, new_hash: bytes | str, **tx_params: Any) -> Any:
        """Propose a new ERC-20 template bytecode hash through the factory precompile."""
        return self._erc20_factory.functions.proposeTemplateUpdate(new_hash).transact(_tx_params(tx_params))

    def execute_erc20_template_update(self, **tx_params: Any) -> Any:
        """Execute the pending ERC-20 template update after its timelock."""
        return self._erc20_factory.functions.executeTemplateUpdate().transact(_tx_params(tx_params))
