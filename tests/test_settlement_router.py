from web3 import Web3

from diesis.settlement.router import (
    encode_deposit,
    encode_set_token_allowed,
    encode_withdraw,
)

_TOKEN = "0x" + "01" * 20
_ACCOUNT = "0x" + "02" * 20


def test_encode_deposit_selector_and_args() -> None:
    calldata = encode_deposit(_TOKEN, 1000, _ACCOUNT)
    selector = "0x" + Web3.keccak(text="deposit(address,uint256,address)").hex()[:8]
    assert calldata.startswith(selector)
    # 4-byte selector + three 32-byte words.
    assert len(bytes.fromhex(calldata[2:])) == 4 + 3 * 32


def test_encode_withdraw_selector() -> None:
    calldata = encode_withdraw(_TOKEN, 2000, _ACCOUNT)
    selector = "0x" + Web3.keccak(text="withdraw(address,uint256,address)").hex()[:8]
    assert calldata.startswith(selector)


def test_encode_set_token_allowed_selector() -> None:
    calldata = encode_set_token_allowed(_TOKEN, True)
    selector = "0x" + Web3.keccak(text="setTokenAllowed(address,bool)").hex()[:8]
    assert calldata.startswith(selector)
    assert len(bytes.fromhex(calldata[2:])) == 4 + 2 * 32
