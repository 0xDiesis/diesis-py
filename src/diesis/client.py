"""DiesisClient — unified entry point for the Diesis Python SDK."""

from __future__ import annotations

from typing import Any

from web3 import Web3
from web3.types import RPCEndpoint

from .bundles.actions import BundleActions
from .chains import Chain, diesis
from .exchange.actions import ExchangeActions
from .intents.signing import sign_order_intent, sign_trading_key_authorization
from .intents.types import OrderIntent, SignedOrderIntent, TradingKeyAuthorization
from .patronage.actions import PatronageActions


class DiesisClient:
    """Main client for interacting with the Diesis chain."""

    def __init__(
        self,
        rpc_url: str | None = None,
        *,
        w3: Web3 | None = None,
        chain: Chain = diesis,
        private_key: str | None = None,
    ) -> None:
        if w3 is not None:
            self._w3 = w3
        elif rpc_url is not None:
            self._w3 = Web3(Web3.HTTPProvider(rpc_url))
        else:
            raise ValueError("Either rpc_url or w3 must be provided")

        self.chain = chain
        self._private_key = private_key
        self.exchange = ExchangeActions(self._w3)
        self.bundles = BundleActions(self._w3)
        self.patronage = PatronageActions(self._w3)

    @property
    def w3(self) -> Web3:
        """Return the underlying Web3 instance."""
        return self._w3

    def _rpc(self, method: str, params: list[Any]) -> Any:
        response = self._w3.provider.make_request(RPCEndpoint(method), params)
        if "error" in response:
            raise RuntimeError(f"RPC error: {response['error']}")
        return response["result"]

    def get_rules(self) -> Any:
        """Fetch chain rules via ``diesis_getRules``."""
        return self._rpc("diesis_getRules", [])

    def get_pipeline_status(self) -> Any:
        """Fetch pipeline status via ``diesis_getPipelineStatus``."""
        return self._rpc("diesis_getPipelineStatus", [])

    def get_transaction_status(self, tx_hash: str) -> Any:
        """Fetch transaction status via ``diesis_getTransactionStatus``."""
        return self._rpc("diesis_getTransactionStatus", [tx_hash])

    def get_block_witness(self, block_hash: str) -> Any:
        """Fetch block witness via ``diesis_getBlockWitness``."""
        return self._rpc("diesis_getBlockWitness", [block_hash])

    def get_block_metadata(self, block_number: int) -> Any:
        """Fetch block metadata via ``diesis_getBlockMetadata``."""
        return self._rpc("diesis_getBlockMetadata", [block_number])

    def get_consensus_commit_status(self, round: int) -> Any:
        """Fetch consensus commit status via ``diesis_getConsensusCommitStatus``."""
        return self._rpc("diesis_getConsensusCommitStatus", [round])

    def _require_key(self) -> str:
        if self._private_key is None:
            raise ValueError("private_key is required for signing operations")
        return self._private_key

    def send_transaction_sync(self, to: str, value: int = 0, data: str = "0x") -> Any:
        """Send a raw transaction synchronously via ``diesis_sendRawTransactionSync``."""
        return self._rpc("diesis_sendRawTransactionSync", [{"to": to, "value": hex(value), "data": data}])

    def sign_order_intent(self, intent: OrderIntent) -> SignedOrderIntent:
        """Sign an order intent using the configured private key."""
        return sign_order_intent(self._require_key(), intent, chain_id=self.chain.id)

    def sign_trading_key_authorization(self, auth: TradingKeyAuthorization) -> str:
        """Sign a trading key authorization using the configured private key."""
        return sign_trading_key_authorization(self._require_key(), auth, chain_id=self.chain.id)

    def submit_intent(self, intent: SignedOrderIntent) -> Any:
        """Submit a signed order intent via ``diesis_submitIntent``."""
        return self._rpc(
            "diesis_submitIntent",
            [
                {
                    "intent": {
                        "marketId": intent.intent.market_id,
                        "side": intent.intent.side,
                        "price": hex(intent.intent.price),
                        "amount": hex(intent.intent.amount),
                        "orderType": intent.intent.order_type,
                        "nonce": hex(intent.intent.nonce),
                        "expiry": hex(intent.intent.expiry),
                        "reduceOnly": intent.intent.reduce_only,
                    },
                    "signature": intent.signature,
                    "signer": intent.signer,
                }
            ],
        )

    def send_stealth_bundle(self, funding_tx: str, announce_tx: str) -> Any:
        """Send a stealth bundle via ``diesis_sendStealthBundle``."""
        return self._rpc("diesis_sendStealthBundle", [{"fundingTx": funding_tx, "announceTx": announce_tx}])
