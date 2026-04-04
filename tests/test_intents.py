from eth_account import Account

from diesis.intents.types import OrderIntent, SignedOrderIntent, TradingKeyAuthorization
from diesis.intents.signing import sign_order_intent, sign_trading_key_authorization

TEST_PRIVATE_KEY = "0x" + "ab" * 32


def test_order_intent_frozen() -> None:
    intent = OrderIntent(
        market_id="0x" + "01" * 32,
        side=0, price=100, amount=50, order_type=0,
        nonce=1, expiry=9999, reduce_only=False,
    )
    assert intent.price == 100
    try:
        intent.price = 200
        raise AssertionError("Should be frozen")
    except AttributeError:
        pass


def test_sign_order_intent_returns_signed() -> None:
    intent = OrderIntent(
        market_id="0x" + "01" * 32,
        side=0, price=100, amount=50, order_type=0,
        nonce=1, expiry=9999, reduce_only=False,
    )
    signed = sign_order_intent(TEST_PRIVATE_KEY, intent)
    assert isinstance(signed, SignedOrderIntent)
    assert signed.intent is intent
    assert signed.signature.startswith("0x")
    assert len(signed.signature) == 132  # 0x + 130 hex chars
    expected_signer = Account.from_key(TEST_PRIVATE_KEY).address
    assert signed.signer == expected_signer


def test_sign_order_intent_deterministic() -> None:
    intent = OrderIntent(
        market_id="0x" + "01" * 32,
        side=0, price=100, amount=50, order_type=0,
        nonce=1, expiry=9999, reduce_only=False,
    )
    sig1 = sign_order_intent(TEST_PRIVATE_KEY, intent)
    sig2 = sign_order_intent(TEST_PRIVATE_KEY, intent)
    assert sig1.signature == sig2.signature


def test_sign_order_intent_different_chain_ids() -> None:
    intent = OrderIntent(
        market_id="0x" + "01" * 32,
        side=0, price=100, amount=50, order_type=0,
        nonce=1, expiry=9999, reduce_only=False,
    )
    sig_mainnet = sign_order_intent(TEST_PRIVATE_KEY, intent, chain_id=1980)
    sig_testnet = sign_order_intent(TEST_PRIVATE_KEY, intent, chain_id=19803)
    assert sig_mainnet.signature != sig_testnet.signature


def test_sign_trading_key_authorization() -> None:
    auth = TradingKeyAuthorization(
        trading_key=Account.from_key(TEST_PRIVATE_KEY).address,
        expiry=9999, max_notional=1_000_000,
        markets=["0x" + "01" * 32],
        can_withdraw=False,
    )
    sig = sign_trading_key_authorization(TEST_PRIVATE_KEY, auth)
    assert sig.startswith("0x")
    assert len(sig) == 132
