from eth_account import Account
from eth_account.messages import encode_typed_data
from web3 import Web3

from diesis.addresses import DIESIS_PERPS_BOOK
from diesis.exchange.signed_perps import (
    actions_hash,
    perps_domain,
    sign_perp_actions,
    signed_perp_actions_typed_data,
)


def test_actions_hash_is_keccak_of_bytes() -> None:
    actions = "0x" + "ab" * 8
    assert actions_hash(actions) == "0x" + Web3.keccak(bytes.fromhex("ab" * 8)).hex()


def test_perps_domain_targets_perps_book() -> None:
    domain = perps_domain()
    assert domain["name"] == "Diesis Exchange"
    assert domain["version"] == "2"
    assert domain["verifyingContract"] == Web3.to_checksum_address(DIESIS_PERPS_BOOK)


def test_signed_perp_actions_recovers_trader() -> None:
    trader = Account.create()
    actions = "0x" + "cafe" * 4
    envelope = sign_perp_actions(trader.key.hex(), trader.address, nonce=7, expiry=0, actions=actions)
    assert envelope.trader == trader.address
    assert envelope.actions_hash == actions_hash(actions)
    typed = signed_perp_actions_typed_data(envelope.trader, envelope.nonce, envelope.expiry, envelope.actions_hash)
    signable = encode_typed_data(
        domain_data=typed["domain"],
        message_types=typed["types"],
        message_data=typed["message"],
    )
    assert Account.recover_message(signable, signature=envelope.signature) == trader.address
