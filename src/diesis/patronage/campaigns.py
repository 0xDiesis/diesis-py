"""Self-service campaign onboarding: EIP-712 vouchers and calldata helpers.

Mirrors ``crates/contracts/src/diesis_patron.rs`` and ``DiesisPatron.sol``. A
campaign owner signs a :class:`CampaignVoucherV1` authorizing one exact, bounded
onboarding route; the beneficiary claims it to install the sponsored grant. The
digest and campaign-id derivation reproduce the contract byte-for-byte so a
voucher signed here verifies on-chain.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from eth_abi.abi import encode as abi_encode
from eth_account import Account
from eth_account.messages import encode_typed_data
from web3 import Web3

from ..addresses import DIESIS_PATRON

_CAMPAIGN_VOUCHER_TYPES = {
    "CampaignVoucherV1": [
        {"name": "campaignId", "type": "bytes32"},
        {"name": "beneficiary", "type": "address"},
        {"name": "target", "type": "address"},
        {"name": "selector", "type": "bytes4"},
        {"name": "maxTransactions", "type": "uint32"},
        {"name": "maxLifetimeSpend", "type": "uint256"},
        {"name": "expiry", "type": "uint64"},
        {"name": "nonce", "type": "uint256"},
    ],
}


@dataclass(frozen=True)
class CampaignVoucherV1:
    """A signed authorization for one exact, bounded onboarding route."""

    campaign_id: str
    beneficiary: str
    target: str
    selector: str
    max_transactions: int
    max_lifetime_spend: int
    expiry: int
    nonce: int


def _bytes_from_hex(field: str, value: str, width: int) -> bytes:
    if not isinstance(value, str) or not value.startswith("0x"):
        raise ValueError(f"{field} must be a 0x-prefixed hex string")
    raw = bytes.fromhex(value[2:])
    if len(raw) != width:
        raise ValueError(f"{field} must be {width} bytes, got {len(raw)}")
    return raw


def campaign_id_for(owner: str, salt: str) -> str:
    """Deterministic owner-bound campaign id: ``keccak256(abi.encode(owner, salt))``.

    Reproduces ``DiesisPatron.campaignIdFor`` so a client can derive the id a
    registration will own before submitting it and bind vouchers to it.
    """
    owner_addr = Web3.to_checksum_address(owner)
    encoded = abi_encode(["address", "bytes32"], [owner_addr, _bytes_from_hex("salt", salt, 32)])
    return "0x" + Web3.keccak(encoded).hex()


def campaign_voucher_domain(chain_id: int = 1980, patron: str = DIESIS_PATRON) -> dict[str, Any]:
    """EIP-712 domain bound to the chain and Patron address."""
    return {
        "name": "DiesisPatron",
        "version": "1",
        "chainId": chain_id,
        "verifyingContract": Web3.to_checksum_address(patron),
    }


def _voucher_message(voucher: CampaignVoucherV1) -> dict[str, Any]:
    return {
        "campaignId": _bytes_from_hex("campaign_id", voucher.campaign_id, 32),
        "beneficiary": Web3.to_checksum_address(voucher.beneficiary),
        "target": Web3.to_checksum_address(voucher.target),
        "selector": _bytes_from_hex("selector", voucher.selector, 4),
        "maxTransactions": voucher.max_transactions,
        "maxLifetimeSpend": voucher.max_lifetime_spend,
        "expiry": voucher.expiry,
        "nonce": voucher.nonce,
    }


def campaign_voucher_typed_data(
    voucher: CampaignVoucherV1,
    chain_id: int = 1980,
    patron: str = DIESIS_PATRON,
) -> dict[str, Any]:
    """Canonical EIP-712 typed data a campaign owner signs to authorize a voucher."""
    return {
        "domain": campaign_voucher_domain(chain_id, patron),
        "types": _CAMPAIGN_VOUCHER_TYPES,
        "primaryType": "CampaignVoucherV1",
        "message": _voucher_message(voucher),
    }


def sign_campaign_voucher(
    private_key: str,
    voucher: CampaignVoucherV1,
    chain_id: int = 1980,
    patron: str = DIESIS_PATRON,
) -> str:
    """Sign a campaign voucher; the returned 0x signature is passed to claim."""
    typed = campaign_voucher_typed_data(voucher, chain_id, patron)
    signable = encode_typed_data(
        domain_data=typed["domain"],
        message_types=typed["types"],
        message_data=typed["message"],
    )
    signed = Account.sign_message(signable, private_key)
    return "0x" + signed.signature.hex()  # type: ignore[no-any-return]


def _selector(signature: str) -> bytes:
    return bytes(Web3.keccak(text=signature)[:4])


def encode_register_campaign(salt: str) -> str:
    """``registerCampaignV1(bytes32 salt)`` calldata (0x hex)."""
    args = abi_encode(["bytes32"], [_bytes_from_hex("salt", salt, 32)])
    return "0x" + (_selector("registerCampaignV1(bytes32)") + args).hex()


def encode_set_campaign_revoked(campaign_id: str, revoked: bool) -> str:
    """``setCampaignRevokedV1(bytes32,bool)`` calldata."""
    args = abi_encode(["bytes32", "bool"], [_bytes_from_hex("campaign_id", campaign_id, 32), revoked])
    return "0x" + (_selector("setCampaignRevokedV1(bytes32,bool)") + args).hex()


def encode_revoke_campaign_voucher(campaign_id: str, beneficiary: str, nonce: int) -> str:
    """``revokeCampaignVoucherV1(bytes32,address,uint256)`` calldata."""
    args = abi_encode(
        ["bytes32", "address", "uint256"],
        [_bytes_from_hex("campaign_id", campaign_id, 32), Web3.to_checksum_address(beneficiary), nonce],
    )
    return "0x" + (_selector("revokeCampaignVoucherV1(bytes32,address,uint256)") + args).hex()


def encode_rotate_campaign_owner(campaign_id: str, new_owner: str) -> str:
    """``rotateCampaignOwnerV1(bytes32,address)`` calldata."""
    args = abi_encode(
        ["bytes32", "address"],
        [_bytes_from_hex("campaign_id", campaign_id, 32), Web3.to_checksum_address(new_owner)],
    )
    return "0x" + (_selector("rotateCampaignOwnerV1(bytes32,address)") + args).hex()


def encode_claim_campaign_voucher(voucher: CampaignVoucherV1, signature: str) -> str:
    """``claimCampaignVoucherV1((...),bytes)`` calldata for a beneficiary claim."""
    voucher_tuple = (
        _bytes_from_hex("campaign_id", voucher.campaign_id, 32),
        Web3.to_checksum_address(voucher.beneficiary),
        Web3.to_checksum_address(voucher.target),
        _bytes_from_hex("selector", voucher.selector, 4),
        voucher.max_transactions,
        voucher.max_lifetime_spend,
        voucher.expiry,
        voucher.nonce,
    )
    args = abi_encode(
        ["(bytes32,address,address,bytes4,uint32,uint256,uint64,uint256)", "bytes"],
        [voucher_tuple, _bytes_from_hex("signature", signature, len(signature) // 2 - 1)],
    )
    selector = _selector("claimCampaignVoucherV1((bytes32,address,address,bytes4,uint32,uint256,uint64,uint256),bytes)")
    return "0x" + (selector + args).hex()
