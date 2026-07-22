"""Calldata helpers for the generic ERC-20 settlement router.

``DiesisSettlementRouter`` is the public entrypoint that moves standard ERC-20
tokens into and out of exchange settlement balances via the settlement
precompile's ``creditRouterDeposit`` / ``debitRouterWithdrawal`` hooks. These
helpers build calldata against ``DIESIS_SETTLEMENT_ROUTER``.
"""

from __future__ import annotations

from eth_abi.abi import encode as abi_encode
from web3 import Web3

from ..addresses import DIESIS_SETTLEMENT_ROUTER

DEPOSIT_SIGNATURE = "deposit(address,uint256,address)"
WITHDRAW_SIGNATURE = "withdraw(address,uint256,address)"
SET_TOKEN_ALLOWED_SIGNATURE = "setTokenAllowed(address,bool)"


def _selector(signature: str) -> bytes:
    return bytes(Web3.keccak(text=signature)[:4])


def _uint256(field: str, value: int) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(f"{field} must be an integer")
    if value < 0 or value >= 1 << 256:
        raise ValueError(f"{field} must fit in uint256")
    return value


def encode_deposit(token: str, amount: int, beneficiary: str) -> str:
    """``deposit(address token, uint256 amount, address beneficiary)`` calldata."""
    selector = _selector(DEPOSIT_SIGNATURE)
    args = abi_encode(
        ["address", "uint256", "address"],
        [Web3.to_checksum_address(token), _uint256("amount", amount), Web3.to_checksum_address(beneficiary)],
    )
    return "0x" + (selector + args).hex()


def encode_withdraw(token: str, amount: int, recipient: str) -> str:
    """``withdraw(address token, uint256 amount, address recipient)`` calldata."""
    selector = _selector(WITHDRAW_SIGNATURE)
    args = abi_encode(
        ["address", "uint256", "address"],
        [Web3.to_checksum_address(token), _uint256("amount", amount), Web3.to_checksum_address(recipient)],
    )
    return "0x" + (selector + args).hex()


def encode_set_token_allowed(token: str, allowed: bool) -> str:
    """``setTokenAllowed(address token, bool allowed)`` calldata."""
    selector = _selector(SET_TOKEN_ALLOWED_SIGNATURE)
    args = abi_encode(["address", "bool"], [Web3.to_checksum_address(token), allowed])
    return "0x" + (selector + args).hex()


__all__ = [
    "DEPOSIT_SIGNATURE",
    "DIESIS_SETTLEMENT_ROUTER",
    "SET_TOKEN_ALLOWED_SIGNATURE",
    "WITHDRAW_SIGNATURE",
    "encode_deposit",
    "encode_set_token_allowed",
    "encode_withdraw",
]
