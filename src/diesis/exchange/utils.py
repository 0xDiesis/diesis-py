"""Exchange utility functions."""
from web3 import Web3


def market_id(base_token: str, quote_token: str, market_type: int = 0) -> str:
    """Compute the canonical market ID from base token, quote token, and market type."""
    return "0x" + Web3.solidity_keccak(
        ["address", "address", "uint8"],
        [base_token, quote_token, market_type],
    ).hex()
