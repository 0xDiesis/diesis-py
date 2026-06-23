"""EIP-712 signing for order intents and trading key authorizations."""

from __future__ import annotations

from typing import Any

from eth_account import Account
from eth_account.messages import encode_typed_data
from web3 import Web3

from ..addresses import DIESIS_SPOT_BOOK
from .types import OrderFlags, OrderIntent, SignedOrderIntent, TradingKeyAuthorization

_ORDER_INTENT_TYPES = {
    "OrderIntent": [
        {"name": "trader", "type": "address"},
        {"name": "marketId", "type": "bytes32"},
        {"name": "side", "type": "uint8"},
        {"name": "orderType", "type": "uint8"},
        {"name": "price", "type": "uint256"},
        {"name": "amount", "type": "uint256"},
        {"name": "triggerPrice", "type": "uint256"},
        {"name": "expiry", "type": "uint64"},
        {"name": "nonce", "type": "uint256"},
        {"name": "flags", "type": "uint8"},
        {"name": "conductor", "type": "address"},
        {"name": "conductorFeeBps", "type": "uint16"},
        {"name": "maxConductorFee", "type": "uint256"},
    ],
}

_TRADING_KEY_TYPES = {
    "TradingKeyAuthorization": [
        {"name": "tradingKey", "type": "address"},
        {"name": "expiry", "type": "uint256"},
        {"name": "maxNotional", "type": "uint256"},
        {"name": "markets", "type": "bytes32[]"},
        {"name": "canWithdraw", "type": "bool"},
    ],
}


def get_order_intent_domain(
    chain_id: int = 1980,
    verifying_contract: str = DIESIS_SPOT_BOOK,
) -> dict[str, Any]:
    """Return the canonical EIP-712 v2 domain for order intents."""
    return {
        "name": "Diesis Exchange",
        "version": "2",
        "chainId": _validate_uint("chain_id", chain_id, 256),
        "verifyingContract": _validate_address("verifying_contract", verifying_contract),
    }


def get_order_intent_typed_data(
    intent: OrderIntent,
    *,
    chain_id: int = 1980,
    verifying_contract: str = DIESIS_SPOT_BOOK,
) -> dict[str, Any]:
    """Return canonical EIP-712 typed data for an order intent."""
    return {
        "domain": get_order_intent_domain(chain_id, verifying_contract),
        "types": _ORDER_INTENT_TYPES,
        "primaryType": "OrderIntent",
        "message": _order_intent_message(intent),
    }


def _trading_key_domain(chain_id: int) -> dict[str, Any]:
    return {
        "name": "Diesis Exchange",
        "version": "2",
        "chainId": _validate_uint("chain_id", chain_id, 256),
    }


def _validate_address(field: str, value: str) -> str:
    if not isinstance(value, str) or not Web3.is_address(value):
        raise ValueError(f"{field} must be an Ethereum address")
    return Web3.to_checksum_address(value)


def _validate_bytes32(field: str, value: str) -> bytes:
    if not isinstance(value, str) or not value.startswith("0x") or len(value) != 66:
        raise ValueError(f"{field} must be a 0x-prefixed bytes32 hex string")
    try:
        return bytes.fromhex(value[2:])
    except ValueError as exc:
        raise ValueError(f"{field} must be a 0x-prefixed bytes32 hex string") from exc


def _validate_uint(field: str, value: int, bits: int) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(f"{field} must be an integer")
    if value < 0 or value >= 1 << bits:
        raise ValueError(f"{field} must fit uint{bits}")
    return value


def _order_intent_message(intent: OrderIntent) -> dict[str, Any]:
    flags = _validate_uint("flags", int(intent.flags), 8)
    known_flags = int(OrderFlags.POST_ONLY | OrderFlags.REDUCE_ONLY | OrderFlags.IOC | OrderFlags.FOK)
    if flags & ~known_flags:
        raise ValueError("flags contains unsupported order behavior bits")
    return {
        "trader": _validate_address("trader", intent.trader),
        "marketId": _validate_bytes32("market_id", intent.market_id),
        "side": _validate_uint("side", int(intent.side), 8),
        "orderType": _validate_uint("order_type", int(intent.order_type), 8),
        "price": _validate_uint("price", intent.price, 256),
        "amount": _validate_uint("amount", intent.amount, 256),
        "triggerPrice": _validate_uint("trigger_price", intent.trigger_price, 256),
        "expiry": _validate_uint("expiry", intent.expiry, 64),
        "nonce": _validate_uint("nonce", intent.nonce, 256),
        "flags": flags,
        "conductor": _validate_address("conductor", intent.conductor),
        "conductorFeeBps": _validate_uint("conductor_fee_bps", intent.conductor_fee_bps, 16),
        "maxConductorFee": _validate_uint("max_conductor_fee", intent.max_conductor_fee, 256),
    }


def sign_order_intent(
    private_key: str,
    intent: OrderIntent,
    chain_id: int = 1980,
    verifying_contract: str = DIESIS_SPOT_BOOK,
) -> SignedOrderIntent:
    """Sign a gasless order intent using canonical EIP-712 v2 typed data."""
    typed_data = get_order_intent_typed_data(
        intent,
        chain_id=chain_id,
        verifying_contract=verifying_contract,
    )
    signable = encode_typed_data(
        domain_data=typed_data["domain"],
        message_types=typed_data["types"],
        message_data=typed_data["message"],
    )
    signed = Account.sign_message(signable, private_key)
    return SignedOrderIntent(
        intent=intent,
        signature="0x" + signed.signature.hex(),
        signer=Account.from_key(private_key).address,
    )


def sign_trading_key_authorization(
    private_key: str,
    auth: TradingKeyAuthorization,
    chain_id: int = 1980,
) -> str:
    """Sign a trading key authorization using EIP-712 v2 typed data."""
    domain = _trading_key_domain(chain_id)
    message = {
        "tradingKey": _validate_address("trading_key", auth.trading_key),
        "expiry": _validate_uint("expiry", auth.expiry, 256),
        "maxNotional": _validate_uint("max_notional", auth.max_notional, 256),
        "markets": [_validate_bytes32("markets[]", m) for m in auth.markets],
        "canWithdraw": auth.can_withdraw,
    }
    signable = encode_typed_data(
        domain_data=domain,
        message_types=_TRADING_KEY_TYPES,
        message_data=message,
    )
    signed = Account.sign_message(signable, private_key)
    return "0x" + signed.signature.hex()  # type: ignore[no-any-return]
