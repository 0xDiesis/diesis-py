"""Staking contract actions for the Diesis Python SDK."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, cast

from web3 import Web3
from web3.contract import Contract
from web3.types import TxParams

from ..abi.generated.DiesisStaking import DIESISSTAKING_ABI
from ..addresses import DIESIS_STAKING


@dataclass(frozen=True)
class ValidatorInfo:
    operator: str
    flags: int
    bonded: int
    joined_checkpoint: int
    joined_at: int
    held_at: int
    held_checkpoint: int


@dataclass(frozen=True)
class PositionInfo:
    validator_id: int
    amount: int
    entry_checkpoint: int


class StakingActions:
    """Read and write actions for the DiesisStaking contract."""

    def __init__(self, w3: Web3) -> None:
        self._w3 = w3
        self._contract: Contract = w3.eth.contract(
            address=Web3.to_checksum_address(DIESIS_STAKING),
            abi=DIESISSTAKING_ABI,
        )

    # ── Read actions ────────────────────────────────────────────────────────

    def get_validator(self, validator_id: int) -> ValidatorInfo:
        """Get validator info by ID."""
        result = self._contract.functions.nodeLedger(validator_id).call()
        return ValidatorInfo(
            operator=result[0],
            flags=result[1],
            bonded=result[2],
            joined_checkpoint=result[3],
            joined_at=result[4],
            held_at=result[5],
            held_checkpoint=result[6],
        )

    def get_position(self, token_id: int) -> PositionInfo:
        """Get position info by token ID."""
        result = self._contract.functions.stakeLots(token_id).call()
        return PositionInfo(
            validator_id=result[0],
            amount=result[1],
            entry_checkpoint=result[2],
        )

    def get_unclaimed_rewards(self, token_id: int) -> int:
        """Get unclaimed rewards for a position."""
        return cast(int, self._contract.functions.unclaimedRewards(token_id).call())

    def get_aggregate_active_stake(self) -> int:
        """Get aggregate active stake."""
        return cast(int, self._contract.functions.aggregateActiveStake().call())

    def get_aggregate_stake(self) -> int:
        """Get aggregate total stake."""
        return cast(int, self._contract.functions.aggregateStake().call())

    def get_latest_finalized_checkpoint(self) -> int:
        """Get the latest finalized checkpoint."""
        return cast(int, self._contract.functions.latestFinalizedCheckpoint().call())

    def get_circulating_supply(self) -> int:
        """Get circulating supply."""
        return cast(int, self._contract.functions.circulatingSupply().call())

    def get_validator_by_address(self, address: str) -> int:
        """Look up validator ID by operator address."""
        return cast(
            int,
            self._contract.functions.nodeIdByOperator(
                Web3.to_checksum_address(address),
            ).call(),
        )

    def is_slashable(self, validator_id: int) -> bool:
        """Check if a validator is a slashable."""
        return cast(bool, self._contract.functions.isSlashable(validator_id).call())

    # ── Write actions ───────────────────────────────────────────────────────

    def stake(self, validator_id: int, amount: int, **tx_params: Any) -> Any:
        """Stake native tokens to a validator. Returns transaction hash."""
        return self._contract.functions.stake(validator_id).transact(
            cast(TxParams, {"value": amount, **tx_params}),
        )

    def request_unstake(self, token_id: int, request_id: int, amount: int, **tx_params: Any) -> Any:
        """Request unstake from a position."""
        return self._contract.functions.requestUnstake(
            token_id,
            request_id,
            amount,
        ).transact(cast(TxParams, tx_params))

    def complete_unstake(self, token_id: int, request_id: int, **tx_params: Any) -> Any:
        """Complete an unstake request after cooldown."""
        return self._contract.functions.completeUnstake(
            token_id,
            request_id,
        ).transact(cast(TxParams, tx_params))

    def harvest_rewards(self, token_id: int, **tx_params: Any) -> Any:
        """Harvest (claim) rewards for a position."""
        return self._contract.functions.harvestRewards(token_id).transact(cast(TxParams, tx_params))

    def compound_rewards(self, token_id: int, **tx_params: Any) -> Any:
        """Compound (restake) rewards for a position."""
        return self._contract.functions.compoundRewards(token_id).transact(cast(TxParams, tx_params))

    def register_validator(self, pubkey: bytes, self_stake: int, **tx_params: Any) -> Any:
        """Register a new validator with a public key and self-stake."""
        return self._contract.functions.registerValidator(pubkey).transact(
            cast(TxParams, {"value": self_stake, **tx_params}),
        )

    def set_validator_commission(self, validator_id: int, rate: int, **tx_params: Any) -> Any:
        """Set per-validator commission rate (validator operator only)."""
        return self._contract.functions.setValidatorCommission(
            validator_id,
            rate,
        ).transact(cast(TxParams, tx_params))

    def withdraw_validator(self, validator_id: int, **tx_params: Any) -> Any:
        """Withdraw a validator and release pubkey for reuse."""
        return self._contract.functions.withdrawValidator(
            validator_id,
        ).transact(cast(TxParams, tx_params))
