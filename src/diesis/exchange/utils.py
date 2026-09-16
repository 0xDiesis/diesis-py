"""Exchange utility functions."""

from web3 import Web3


def _bytes32(field: str, value: str) -> bytes:
    if not isinstance(value, str) or not value.startswith("0x") or len(value) != 66:
        raise ValueError(f"{field} must be a 0x-prefixed bytes32 hex string")
    return bytes.fromhex(value[2:])


def market_id(base_token: str, quote_token: str, market_type: int = 0) -> str:
    """Compute the canonical market ID from base token, quote token, and market type."""
    return (  # type: ignore[no-any-return]
        "0x"
        + Web3.solidity_keccak(
            ["address", "address", "uint8"],
            [base_token, quote_token, market_type],
        ).hex()
    )
