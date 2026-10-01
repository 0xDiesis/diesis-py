"""DiesisClient — unified entry point for the Diesis Python SDK."""

from __future__ import annotations

import re
from typing import Any

from web3 import Web3

from ._rpc import _rpc
from .bundles.actions import BundleActions
from .chains import Chain, diesis
from .exchange.actions import ExchangeActions
from .intents.signing import sign_order_intent, sign_trading_key_authorization
from .intents.types import OrderIntent, SignedOrderIntent, TradingKeyAuthorization
from .patronage.actions import PatronageActions
from .privacy.actions import PrivacyActions
from .staking.actions import StakingActions


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
        self.privacy = PrivacyActions(self._w3)
        self.staking = StakingActions(self._w3)

    @property
    def w3(self) -> Web3:
        """Return the underlying Web3 instance."""
        return self._w3

    def get_rules(self) -> Any:
        """Fetch chain rules via ``diesis_getRules``."""
        return _rpc(self._w3, "diesis_getRules", [])

    def get_runtime_capabilities(self) -> Any:
        """Return actual node execution capabilities; this is not signing authority."""
        return _rpc(self._w3, "diesis_getRuntimeCapabilities", [])

    def get_pipeline_status(self) -> Any:
        """Return node pipeline heads, lags, queue depths and backpressure mode.

        Values describe local processing, not certified finality.
        """
        return _rpc(self._w3, "diesis_getPipelineStatus", [])

    def get_block_witness(self, block_hash: str) -> str | None:
        """Return unverified serialized witness bytes as hex, or None.

        This transport does not validate the witness or its block commitment.
        """
        if not isinstance(block_hash, str) or not re.fullmatch(r"0x[0-9a-fA-F]{64}", block_hash):
            raise ValueError("Block witness requires a 32-byte block hash")
        result = _rpc(self._w3, "diesis_getBlockWitness", [block_hash])
        if result is None:
            return None
        if not isinstance(result, str) or not re.fullmatch(r"0x(?:[0-9a-fA-F]{2})*", result):
            raise ValueError("Invalid block witness bytes response")
        return result

    def get_transaction_status(self, tx_hash: str) -> Any:
        """Fetch transaction status via ``diesis_getTransactionStatus``."""
        return _rpc(self._w3, "diesis_getTransactionStatus", [tx_hash])

    def get_transaction_lifecycle(self, tx_hash: str) -> Any:
        """Return lifecycle and orphaned/replaced lineage, or None when unknown."""
        return _rpc(self._w3, "diesis_getTransactionLifecycle", [tx_hash])

    def get_exchange_action_status(self, action_hash: str) -> Any:
        """Query relay action identity, which is distinct from an EVM transaction hash."""
        return _rpc(self._w3, "diesis_getExchangeActionStatus", [action_hash])

    def get_block_metadata(self, block_number: int) -> Any:
        """Fetch block metadata via ``diesis_getBlockMetadata``."""
        return _rpc(self._w3, "diesis_getBlockMetadata", [_safe_rpc_integer(block_number)])

    def get_consensus_commit_status(self, round: int) -> Any:
        """Fetch consensus commit status via ``diesis_getConsensusCommitStatus``."""
        return _rpc(self._w3, "diesis_getConsensusCommitStatus", [_safe_rpc_integer(round)])

    def _require_key(self) -> str:
        if self._private_key is None:
            raise ValueError("private_key is required for signing operations")
        return self._private_key

    def send_transaction_sync(self, serialized_transaction_hex: str) -> Any:
        """Submit whole serialized signed bytes and return the node's direct receipt.

        Byte framing is validated here; decoding, signature validity and admission
        remain node responsibilities. A receipt is not finalized inclusion proof.
        """
        if not isinstance(serialized_transaction_hex, str) or not re.fullmatch(
            r"0x(?:[0-9a-fA-F]{2})+", serialized_transaction_hex
        ):
            raise ValueError("Sync submission requires whole serialized signed transaction bytes")
        return _rpc(self._w3, "diesis_sendRawTransactionSync", [serialized_transaction_hex])

    def sign_order_intent(self, intent: OrderIntent) -> SignedOrderIntent:
        """Sign an order intent using the configured private key."""
        return sign_order_intent(self._require_key(), intent, chain_id=self.chain.id)

    def sign_trading_key_authorization(self, auth: TradingKeyAuthorization) -> str:
        """Sign a trading key authorization using the configured private key."""
        return sign_trading_key_authorization(self._require_key(), auth, chain_id=self.chain.id)

    def submit_intent(self, intent: SignedOrderIntent) -> Any:
        """Submit a signed order intent via ``diesis_submitIntent``."""
        return _rpc(
            self._w3,
            "diesis_submitIntent",
            [
                {
                    "intent": {
                        "trader": intent.intent.trader,
                        "marketId": intent.intent.market_id,
                        "side": intent.intent.side,
                        "orderType": intent.intent.order_type,
                        "price": hex(intent.intent.price),
                        "amount": hex(intent.intent.amount),
                        "triggerPrice": hex(intent.intent.trigger_price),
                        "expiry": hex(intent.intent.expiry),
                        "nonce": hex(intent.intent.nonce),
                        "flags": intent.intent.flags,
                        "conductor": intent.intent.conductor,
                        "conductorFeeBps": intent.intent.conductor_fee_bps,
                        "maxConductorFee": hex(intent.intent.max_conductor_fee),
                    },
                    "signature": intent.signature,
                    "signer": intent.signer,
                }
            ],
        )


def _safe_rpc_integer(value: int) -> int:
    """Node u64 parameters must also survive JSON consumers without precision loss."""
    if type(value) is not int or value < 0 or value > 2**53 - 1:
        raise ValueError("RPC integer must be between zero and the maximum safe JSON integer")
    return value
