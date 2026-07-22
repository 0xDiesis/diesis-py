from eth_account import Account
from eth_account.messages import encode_typed_data
from web3 import Web3

from diesis.addresses import DIESIS_PATRON
from diesis.patronage import (
    CampaignVoucherV1,
    campaign_id_for,
    campaign_voucher_typed_data,
    encode_claim_campaign_voucher,
    encode_register_campaign,
    encode_rotate_campaign_owner,
    encode_set_campaign_revoked,
    sign_campaign_voucher,
)


def _voucher(campaign_id: str) -> CampaignVoucherV1:
    return CampaignVoucherV1(
        campaign_id=campaign_id,
        beneficiary="0x" + "be" * 20,
        target="0x" + "cd" * 20,
        selector="0xdeadbeef",
        max_transactions=5,
        max_lifetime_spend=10**18,
        expiry=0,
        nonce=1,
    )


def test_campaign_id_for_is_deterministic_and_owner_bound() -> None:
    owner = "0x00000000000000000000000000000000000000AA"
    salt = "0x" + "3c" * 32
    cid = campaign_id_for(owner, salt)
    assert cid == campaign_id_for(owner, salt)
    assert len(cid) == 66
    # A different owner deriving the same salt gets a distinct id.
    other = "0x00000000000000000000000000000000000000BB"
    assert campaign_id_for(other, salt) != cid


def test_campaign_id_for_matches_abi_encode() -> None:
    owner = "0x00000000000000000000000000000000000000AA"
    salt = "0x" + "3c" * 32
    expected = "0x" + Web3.keccak(bytes.fromhex(owner[2:].rjust(64, "0")) + bytes.fromhex(salt[2:])).hex()
    assert campaign_id_for(owner, salt) == expected


def test_voucher_signer_recovers_to_owner() -> None:
    owner = Account.create()
    cid = campaign_id_for(owner.address, "0x" + "3c" * 32)
    voucher = _voucher(cid)
    signature = sign_campaign_voucher(owner.key.hex(), voucher)
    typed = campaign_voucher_typed_data(voucher)
    signable = encode_typed_data(
        domain_data=typed["domain"],
        message_types=typed["types"],
        message_data=typed["message"],
    )
    assert Account.recover_message(signable, signature=signature) == owner.address
    assert typed["domain"]["name"] == "DiesisPatron"
    assert typed["domain"]["verifyingContract"] == Web3.to_checksum_address(DIESIS_PATRON)


def test_calldata_encoders_carry_selectors() -> None:
    salt = "0x" + "3c" * 32
    cid = campaign_id_for("0x" + "aa" * 20, salt)
    voucher = _voucher(cid)
    sig = "0x" + "11" * 65

    reg = encode_register_campaign(salt)
    assert reg.startswith("0x" + Web3.keccak(text="registerCampaignV1(bytes32)").hex()[:8])

    revoke = encode_set_campaign_revoked(cid, True)
    assert revoke.startswith("0x" + Web3.keccak(text="setCampaignRevokedV1(bytes32,bool)").hex()[:8])

    rotate = encode_rotate_campaign_owner(cid, "0x" + "bb" * 20)
    assert rotate.startswith("0x" + Web3.keccak(text="rotateCampaignOwnerV1(bytes32,address)").hex()[:8])

    claim = encode_claim_campaign_voucher(voucher, sig)
    expected = Web3.keccak(
        text="claimCampaignVoucherV1((bytes32,address,address,bytes4,uint32,uint256,uint64,uint256),bytes)"
    ).hex()[:8]
    assert claim.startswith("0x" + expected)
