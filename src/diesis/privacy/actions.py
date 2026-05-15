"""Privacy contract actions for the Diesis Python SDK."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, cast

from web3 import Web3
from web3.contract import Contract
from web3.types import TxParams

from ..abi.generated.DiesisPrivacyPools import DIESISPRIVACYPOOLS_ABI
from ..abi.generated.DiesisShieldedPool import DIESISSHIELDEDPOOL_ABI
from ..addresses import PRIVACY_POOLS, SHIELDED_POOL

ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"


@dataclass(frozen=True)
class ShieldedPoolState:
    denomination: int
    depth: int
    max_leaves: int
    root_history_size: int
    bootstrap_owner: str
    current_root_index: int
    initialized: bool
    next_index: int
    root: bytes
    tree_initialized: bool
    verifier: str


@dataclass(frozen=True)
class PrivacyProvider:
    name: str
    registered: bool
    association_set_root: bytes


class PrivacyActions:
    """Read and write actions for Diesis privacy contracts."""

    def __init__(self, w3: Web3) -> None:
        self._w3 = w3
        self._shielded_pool: Contract = w3.eth.contract(
            address=Web3.to_checksum_address(SHIELDED_POOL),
            abi=DIESISSHIELDEDPOOL_ABI,
        )
        self._privacy_pools: Contract = w3.eth.contract(
            address=Web3.to_checksum_address(PRIVACY_POOLS),
            abi=DIESISPRIVACYPOOLS_ABI,
        )

    @staticmethod
    def _tx_params(tx_params: dict[str, Any]) -> TxParams:
        normalized = dict(tx_params)
        if "from_" in normalized:
            normalized["from"] = normalized.pop("from_")
        return cast(TxParams, normalized)

    # ── Shielded pool reads ─────────────────────────────────────────────────

    def get_shielded_pool_state(self) -> ShieldedPoolState:
        """Read the current shielded pool state summary."""
        return ShieldedPoolState(
            denomination=cast(int, self._shielded_pool.functions.DENOMINATION().call()),
            depth=cast(int, self._shielded_pool.functions.DEPTH().call()),
            max_leaves=cast(int, self._shielded_pool.functions.MAX_LEAVES().call()),
            root_history_size=cast(int, self._shielded_pool.functions.ROOT_HISTORY_SIZE().call()),
            bootstrap_owner=cast(str, self._shielded_pool.functions.bootstrapOwner().call()),
            current_root_index=cast(int, self._shielded_pool.functions.currentRootIndex().call()),
            initialized=cast(bool, self._shielded_pool.functions.initialized().call()),
            next_index=cast(int, self._shielded_pool.functions.nextIndex().call()),
            root=cast(bytes, self._shielded_pool.functions.root().call()),
            tree_initialized=cast(bool, self._shielded_pool.functions.treeInitialized().call()),
            verifier=cast(str, self._shielded_pool.functions.verifierAddr().call()),
        )

    def get_shielded_pool_root(self) -> bytes:
        """Read the current shielded pool Merkle root."""
        return cast(bytes, self._shielded_pool.functions.root().call())

    def is_known_shielded_root(self, root: bytes) -> bool:
        """Check whether a shielded pool root is in recent history."""
        return cast(bool, self._shielded_pool.functions.isKnownRoot(root).call())

    def is_shielded_nullifier_spent(self, nullifier: bytes) -> bool:
        """Check whether a shielded pool nullifier has already been spent."""
        return cast(bool, self._shielded_pool.functions.nullifiers(nullifier).call())

    def get_shielded_root_history(self, index: int) -> bytes:
        """Read a shielded pool root-history entry."""
        return cast(bytes, self._shielded_pool.functions.rootHistory(index).call())

    # ── Privacy pools reads ─────────────────────────────────────────────────

    def get_privacy_provider(self, provider: str) -> PrivacyProvider:
        """Read a privacy-pool provider registration."""
        result = self._privacy_pools.functions.providers(Web3.to_checksum_address(provider)).call()
        return PrivacyProvider(
            name=cast(str, result[0]),
            registered=cast(bool, result[1]),
            association_set_root=cast(bytes, result[2]),
        )

    def get_privacy_provider_count(self) -> int:
        """Read the number of registered privacy-pool providers."""
        return cast(int, self._privacy_pools.functions.providerCount().call())

    def get_privacy_provider_address(self, index: int) -> str:
        """Read a provider address by index."""
        return cast(str, self._privacy_pools.functions.providerList(index).call())

    def get_privacy_pools_owner(self) -> str:
        """Read the privacy-pools owner."""
        return cast(str, self._privacy_pools.functions.owner().call())

    def get_privacy_pools_verifier(self) -> str:
        """Read the privacy-pools verifier address."""
        return cast(str, self._privacy_pools.functions.verifierAddr().call())

    # ── Shielded pool writes ────────────────────────────────────────────────

    def deposit_shielded(self, commitment: bytes, value: int, **tx_params: Any) -> Any:
        """Deposit native tokens and create a shielded commitment."""
        return self._shielded_pool.functions.deposit(commitment).transact(
            self._tx_params({"value": value, **tx_params}),
        )

    def transact_shielded(
        self,
        *,
        proof: bytes,
        merkle_root: bytes,
        nullifiers: list[bytes],
        commitments: list[bytes],
        ext_data_hash: bytes,
        **tx_params: Any,
    ) -> Any:
        """Execute a private transfer inside the shielded pool."""
        return self._shielded_pool.functions.transact(
            proof,
            merkle_root,
            nullifiers,
            commitments,
            ext_data_hash,
        ).transact(self._tx_params(tx_params))

    def withdraw_shielded(
        self,
        *,
        proof: bytes,
        merkle_root: bytes,
        nullifier_hash: bytes,
        recipient: str,
        amount: int,
        relayer: str = ZERO_ADDRESS,
        fee: int = 0,
        **tx_params: Any,
    ) -> Any:
        """Withdraw from the shielded pool."""
        return self._shielded_pool.functions.withdraw(
            proof,
            merkle_root,
            nullifier_hash,
            Web3.to_checksum_address(recipient),
            amount,
            Web3.to_checksum_address(relayer),
            fee,
        ).transact(self._tx_params(tx_params))

    # ── Privacy pools writes ────────────────────────────────────────────────

    def register_privacy_provider(self, provider: str, name: str, **tx_params: Any) -> Any:
        """Register a compliance provider."""
        return self._privacy_pools.functions.registerProvider(
            Web3.to_checksum_address(provider),
            name,
        ).transact(self._tx_params(tx_params))

    def update_association_set(self, new_root: bytes, **tx_params: Any) -> Any:
        """Update the caller provider's association-set root."""
        return self._privacy_pools.functions.updateAssociationSet(new_root).transact(
            self._tx_params(tx_params),
        )

    def verify_association(
        self,
        *,
        proof: bytes,
        association_set_root: bytes,
        nullifier: bytes,
        provider: str,
        **tx_params: Any,
    ) -> Any:
        """Submit an association-set proof verification transaction."""
        return self._privacy_pools.functions.verifyAssociation(
            proof,
            association_set_root,
            nullifier,
            Web3.to_checksum_address(provider),
        ).transact(self._tx_params(tx_params))

    def transfer_privacy_pools_ownership(self, new_owner: str, **tx_params: Any) -> Any:
        """Transfer privacy-pools ownership."""
        return self._privacy_pools.functions.transferOwnership(
            Web3.to_checksum_address(new_owner),
        ).transact(self._tx_params(tx_params))
