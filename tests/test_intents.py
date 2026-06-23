import pytest
from eth_account import Account

from diesis.addresses import DIESIS_SPOT_BOOK
from diesis.intents.signing import (
    get_order_intent_typed_data,
    sign_order_intent,
    sign_trading_key_authorization,
)
from diesis.intents.types import OrderFlags, OrderIntent, SignedOrderIntent, TradingKeyAuthorization

TEST_PRIVATE_KEY = "0x" + "ab" * 32
TEST_TRADER = Account.from_key(TEST_PRIVATE_KEY).address


def sample_order_intent() -> OrderIntent:
    return OrderIntent(
        trader=TEST_TRADER,
        market_id="0x" + "01" * 32,
        side=0,
        order_type=0,
        price=100,
        amount=50,
        nonce=1,
        expiry=9999,
        flags=int(OrderFlags.REDUCE_ONLY),
    )


def test_order_intent_frozen() -> None:
    intent = sample_order_intent()
    assert intent.price == 100
    try:
        intent.price = 200
        raise AssertionError("Should be frozen")
    except AttributeError:
        pass


def test_sign_order_intent_returns_signed() -> None:
    intent = sample_order_intent()
    signed = sign_order_intent(TEST_PRIVATE_KEY, intent)
    assert isinstance(signed, SignedOrderIntent)
    assert signed.intent is intent
    assert signed.signature.startswith("0x")
    assert len(signed.signature) == 132  # 0x + 130 hex chars
    expected_signer = Account.from_key(TEST_PRIVATE_KEY).address
    assert signed.signer == expected_signer


def test_sign_order_intent_deterministic() -> None:
    intent = sample_order_intent()
    sig1 = sign_order_intent(TEST_PRIVATE_KEY, intent)
    sig2 = sign_order_intent(TEST_PRIVATE_KEY, intent)
    assert sig1.signature == sig2.signature


def test_sign_order_intent_different_chain_ids() -> None:
    intent = sample_order_intent()
    sig_mainnet = sign_order_intent(TEST_PRIVATE_KEY, intent, chain_id=1980)
    sig_testnet = sign_order_intent(TEST_PRIVATE_KEY, intent, chain_id=19803)
    assert sig_mainnet.signature != sig_testnet.signature


def test_order_intent_typed_data_matches_v2_shape() -> None:
    typed_data = get_order_intent_typed_data(sample_order_intent())

    assert typed_data["domain"] == {
        "name": "Diesis Exchange",
        "version": "2",
        "chainId": 1980,
        "verifyingContract": DIESIS_SPOT_BOOK,
    }
    assert typed_data["primaryType"] == "OrderIntent"
    assert [field["name"] for field in typed_data["types"]["OrderIntent"]] == [
        "trader",
        "marketId",
        "side",
        "orderType",
        "price",
        "amount",
        "triggerPrice",
        "expiry",
        "nonce",
        "flags",
        "conductor",
        "conductorFeeBps",
        "maxConductorFee",
    ]
    assert typed_data["message"]["trader"] == TEST_TRADER
    assert typed_data["message"]["flags"] == int(OrderFlags.REDUCE_ONLY)
    assert typed_data["message"]["conductor"] == "0x0000000000000000000000000000000000000000"


def test_order_intent_rejects_invalid_hex_fields() -> None:
    bad_market = OrderIntent(
        trader=TEST_TRADER,
        market_id="0x1234",
        side=0,
        order_type=0,
        price=100,
        amount=50,
        nonce=1,
    )
    with pytest.raises(ValueError, match="market_id"):
        get_order_intent_typed_data(bad_market)

    bad_trader = OrderIntent(
        trader="not-an-address",
        market_id="0x" + "01" * 32,
        side=0,
        order_type=0,
        price=100,
        amount=50,
        nonce=1,
    )
    with pytest.raises(ValueError, match="trader"):
        get_order_intent_typed_data(bad_trader)


def test_order_intent_rejects_uint_overflows_and_unknown_flags() -> None:
    with pytest.raises(ValueError, match="expiry"):
        get_order_intent_typed_data(
            OrderIntent(
                trader=TEST_TRADER,
                market_id="0x" + "01" * 32,
                side=0,
                order_type=0,
                price=100,
                amount=50,
                nonce=1,
                expiry=1 << 64,
            )
        )

    with pytest.raises(ValueError, match="unsupported"):
        get_order_intent_typed_data(
            OrderIntent(
                trader=TEST_TRADER,
                market_id="0x" + "01" * 32,
                side=0,
                order_type=0,
                price=100,
                amount=50,
                nonce=1,
                flags=1 << 7,
            )
        )


def test_sign_trading_key_authorization() -> None:
    auth = TradingKeyAuthorization(
        trading_key=Account.from_key(TEST_PRIVATE_KEY).address,
        expiry=9999,
        max_notional=1_000_000,
        markets=["0x" + "01" * 32],
        can_withdraw=False,
    )
    sig = sign_trading_key_authorization(TEST_PRIVATE_KEY, auth)
    assert sig.startswith("0x")
    assert len(sig) == 132


def test_trading_key_authorization_rejects_bad_market_id() -> None:
    auth = TradingKeyAuthorization(
        trading_key=Account.from_key(TEST_PRIVATE_KEY).address,
        expiry=9999,
        max_notional=1_000_000,
        markets=["0x01"],
        can_withdraw=False,
    )
    with pytest.raises(ValueError, match="markets"):
        sign_trading_key_authorization(TEST_PRIVATE_KEY, auth)
