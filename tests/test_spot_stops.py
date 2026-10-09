import pytest
from eth_account import Account
from eth_account.messages import encode_typed_data
from web3 import Web3

from diesis.exchange.spot_stops import (
    STOP_ORDER_TRIGGERED_TOPIC,
    CancelAllSpotIntent,
    cancel_all_typed_data,
    encode_trigger_spot_stops,
    sign_cancel_all_spot_intent,
)
from diesis.intents.signing import get_order_intent_typed_data
from diesis.intents.types import OrderIntent

# Fixed shared vectors from contracts/test/exchange/ExchangePrecompileInterfaces.t.sol.
_CANCEL_ALL_DIGEST = "0xb255e856ada29ff3027cc87677dec35a7fc56ede829135704f186c8f30177ad4"
_STOP_ORDER_DIGEST = "0x17f4cc7860e79c25ed2dbc729a33002c04428bb45739ff5f4758bbae079f67a9"


@pytest.mark.parametrize("market_id", ["0x", "0x12", "0x" + "22" * 31, "0x" + "22" * 33, "22" * 32])
def test_cancel_all_rejects_malformed_market_id(market_id: str) -> None:
    intent = CancelAllSpotIntent(
        trader="0x0000000000000000000000000000000000000001",
        market_id=market_id,
        expiry=0,
        nonce=1,
    )
    with pytest.raises(ValueError, match="market_id must be a 0x-prefixed bytes32 hex string"):
        cancel_all_typed_data(intent)


def _digest(typed: dict) -> str:
    signable = encode_typed_data(
        domain_data=typed["domain"],
        message_types=typed["types"],
        message_data=typed["message"],
    )
    return "0x" + Web3.keccak(b"\x19\x01" + signable.header + signable.body).hex()


def test_cancel_all_digest_fixed_vector() -> None:
    intent = CancelAllSpotIntent(
        trader="0x00000000000000000000000000000000000000AA",
        market_id="0x" + "22" * 32,
        expiry=0,
        nonce=10,
    )
    assert _digest(cancel_all_typed_data(intent)) == _CANCEL_ALL_DIGEST


def test_stop_order_intent_digest_fixed_vector() -> None:
    # A protected stop-limit (orderType = 2) carrying a nonzero price and trigger.
    intent = OrderIntent(
        trader="0x00000000000000000000000000000000000000AA",
        market_id="0x" + "22" * 32,
        side=0,
        order_type=2,
        price=5000,
        amount=100,
        trigger_price=4900,
        expiry=0,
        nonce=10,
        flags=0,
        conductor="0x" + "00" * 20,
        conductor_fee_bps=0,
        max_conductor_fee=0,
    )
    assert _digest(get_order_intent_typed_data(intent)) == _STOP_ORDER_DIGEST


def test_sign_cancel_all_envelope_shape() -> None:
    acct = Account.create()
    intent = CancelAllSpotIntent(
        trader=acct.address,
        market_id="0x" + "22" * 32,
        expiry=0,
        nonce=1,
    )
    envelope = sign_cancel_all_spot_intent(acct.key.hex(), intent)
    assert envelope.intent is intent
    signable = encode_typed_data(
        domain_data=cancel_all_typed_data(intent)["domain"],
        message_types=cancel_all_typed_data(intent)["types"],
        message_data=cancel_all_typed_data(intent)["message"],
    )
    assert Account.recover_message(signable, signature=envelope.signature) == acct.address


def test_trigger_spot_stops_calldata() -> None:
    calldata = encode_trigger_spot_stops("0x" + "22" * 32, 8)
    selector = "0x" + Web3.keccak(text="triggerSpotStops(bytes32,uint16)").hex()[:8]
    assert calldata.startswith(selector)


def test_stop_order_triggered_topic() -> None:
    topic = STOP_ORDER_TRIGGERED_TOPIC
    assert topic == "0x" + Web3.keccak(text="StopOrderTriggered(bytes32,bytes32,address,uint256,uint256)").hex()
