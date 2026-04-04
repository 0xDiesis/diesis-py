"""EIP-712 signing for order intents and trading key authorizations."""

from __future__ import annotations

from typing import Any

from eth_account import Account
from eth_account.messages import encode_typed_data

from .types import OrderIntent, SignedOrderIntent, TradingKeyAuthorization

_ORDER_INTENT_TYPES = {
    "OrderIntent": [
        {"name": "marketId", "type": "bytes32"},
        {"name": "side", "type": "uint8"},
        {"name": "price", "type": "uint256"},
        {"name": "amount", "type": "uint256"},
        {"name": "orderType", "type": "uint8"},
        {"name": "nonce", "type": "uint256"},
        {"name": "expiry", "type": "uint256"},
        {"name": "reduceOnly", "type": "bool"},
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


def _get_domain(chain_id: int) -> dict[str, Any]:
    return {"name": "Diesis Exchange", "version": "1", "chainId": chain_id}


def sign_order_intent(private_key: str, intent: OrderIntent, chain_id: int = 1980) -> SignedOrderIntent:
    """Sign a gasless order intent using EIP-712 typed data."""
    domain = _get_domain(chain_id)
    message = {
        "marketId": bytes.fromhex(intent.market_id[2:]),
        "side": intent.side,
        "price": intent.price,
        "amount": intent.amount,
        "orderType": intent.order_type,
        "nonce": intent.nonce,
        "expiry": intent.expiry,
        "reduceOnly": intent.reduce_only,
    }
    signable = encode_typed_data(
        domain_data=domain,
        message_types=_ORDER_INTENT_TYPES,
        message_data=message,
    )
    signed = Account.sign_message(signable, private_key)
    return SignedOrderIntent(
        intent=intent,
        signature="0x" + signed.signature.hex(),
        signer=Account.from_key(private_key).address,
    )


def sign_trading_key_authorization(private_key: str, auth: TradingKeyAuthorization, chain_id: int = 1980) -> str:
    """Sign a trading key authorization using EIP-712 typed data."""
    domain = _get_domain(chain_id)
    message = {
        "tradingKey": auth.trading_key,
        "expiry": auth.expiry,
        "maxNotional": auth.max_notional,
        "markets": [bytes.fromhex(m[2:]) for m in auth.markets],
        "canWithdraw": auth.can_withdraw,
    }
    signable = encode_typed_data(
        domain_data=domain,
        message_types=_TRADING_KEY_TYPES,
        message_data=message,
    )
    signed = Account.sign_message(signable, private_key)
    return "0x" + signed.signature.hex()  # type: ignore[no-any-return]
