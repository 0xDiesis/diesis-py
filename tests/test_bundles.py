from unittest.mock import MagicMock

import pytest
from eth_account import Account
from eth_account.messages import encode_typed_data
from web3 import Web3

from diesis.bundles import (
    DIESIS_BUNDLE_ESCROW,
    BundleActions,
    BundleManifestEntry,
    BundlePaymentTerms,
    BundlePlanV2,
    ExecutionFlags,
    canonical_bundle_v2,
    consent_typed_data,
    encode_reserve_bundle_v2,
    flags_from_wire,
    flags_to_wire,
    plan_hash,
    plan_to_wire,
    reservation_value,
    sign_member_consent,
)

# Cross-language frozen fixed vector from docs/spec/bundles.md.
_VECTOR_PLAN_HASH = "0x1c064f8de7f925f6dbb68e8d99a780f2f187f8b07ed1905edae77291ad30ddca"


def _vector_plan() -> BundlePlanV2:
    return BundlePlanV2(
        chain_id=8080,
        expiry=1_800_000_000,
        flags=ExecutionFlags.HALT_ON_INVALID | ExecutionFlags.PARTIAL_REFUND,
        payment=BundlePaymentTerms(
            payer="0x" + "11" * 20,
            maximum_builder_payment=1_000_000_000_000,
            refund_gas_price=7,
            maximum_refund=500_000,
            escrow_nonce=42,
        ),
        ordered_members=[
            BundleManifestEntry("0x" + "aa" * 32, 100_000),
            BundleManifestEntry("0x" + "bb" * 32, 250_000),
        ],
    )


def test_execution_flags_values() -> None:
    assert ExecutionFlags.STOP_ON_SUCCESS == 0x01
    assert ExecutionFlags.TOLERATE_INVALID == 0x02
    assert ExecutionFlags.HALT_ON_INVALID == 0x04
    assert ExecutionFlags.PARTIAL_REFUND == 0x08


def test_plan_hash_fixed_vector() -> None:
    """The canonical encoder and plan hash reproduce the cross-language vector."""
    plan = _vector_plan()
    canonical = canonical_bundle_v2(plan)
    # Fixed-width, big-endian, length-prefixed (no member index in the encoding).
    assert canonical[:8] == (8080).to_bytes(8, "big")
    assert plan_hash(plan) == _VECTOR_PLAN_HASH


def test_plan_hash_is_domain_separated() -> None:
    plan = _vector_plan()
    tagged = plan_hash(plan)
    untagged = "0x" + Web3.keccak(canonical_bundle_v2(plan)).hex()
    assert tagged != untagged


def test_plan_hash_binds_member_order() -> None:
    plan = _vector_plan()
    reordered = BundlePlanV2(
        chain_id=plan.chain_id,
        expiry=plan.expiry,
        flags=plan.flags,
        payment=plan.payment,
        ordered_members=list(reversed(plan.ordered_members)),
    )
    assert plan_hash(plan) != plan_hash(reordered)


def test_flags_to_wire_bitflags_string() -> None:
    assert flags_to_wire(ExecutionFlags.HALT_ON_INVALID | ExecutionFlags.PARTIAL_REFUND) == (
        "HALT_ON_INVALID | PARTIAL_REFUND"
    )
    assert flags_to_wire(0) == ""
    assert flags_from_wire("HALT_ON_INVALID | PARTIAL_REFUND") == 0x0C
    with pytest.raises(ValueError):
        flags_to_wire(0x10)


def test_plan_to_wire_camel_case_and_hex() -> None:
    wire = plan_to_wire(_vector_plan())
    assert wire["chainId"] == 8080
    assert wire["flags"] == "HALT_ON_INVALID | PARTIAL_REFUND"
    assert wire["payment"]["maximumBuilderPayment"] == hex(1_000_000_000_000)
    assert wire["orderedMembers"][0]["gasAllowance"] == 100_000


def test_reserve_bundle_v2_calldata_and_value() -> None:
    plan = _vector_plan()
    calldata = encode_reserve_bundle_v2(plan)
    selector = "0x" + Web3.keccak(text="reserveBundleV2(bytes32,uint256,uint256,uint256,uint256,uint64)").hex()[:8]
    assert calldata.startswith(selector)
    assert plan_hash(plan)[2:] in calldata
    assert reservation_value(plan) == 1_000_000_000_000 + 500_000


def test_sign_member_consent_roundtrip() -> None:
    acct = Account.create()
    plan = _vector_plan()
    consent = sign_member_consent(acct.key.hex(), plan, member_index=1)
    assert consent.signer == acct.address
    assert consent.member_index == 1
    assert consent.plan_hash == _VECTOR_PLAN_HASH
    typed = consent_typed_data(consent.plan_hash, 1, consent.transaction_hash, plan.chain_id)
    signable = encode_typed_data(
        domain_data=typed["domain"],
        message_types=typed["types"],
        message_data=typed["message"],
    )
    assert Account.recover_message(signable, signature=consent.signature) == acct.address
    assert typed["domain"]["verifyingContract"] == Web3.to_checksum_address(DIESIS_BUNDLE_ESCROW)


def test_prepare_bundle_v2_wire() -> None:
    mock_w3 = MagicMock()
    mock_w3.provider.make_request.return_value = {
        "result": {"planHash": _VECTOR_PLAN_HASH, "version": 2, "memberDigests": ["0x" + "01" * 32]}
    }
    actions = BundleActions(mock_w3)
    result = actions.prepare_bundle(_vector_plan())
    call = mock_w3.provider.make_request.call_args
    assert call[0][0] == "diesis_prepareBundle"
    assert call[0][1][0]["plan"]["chainId"] == 8080
    assert result.version == 2
    assert result.member_digests == ["0x" + "01" * 32]


def test_get_bundle_status_v2_fields() -> None:
    mock_w3 = MagicMock()
    mock_w3.provider.make_request.return_value = {
        "result": {
            "planHash": _VECTOR_PLAN_HASH,
            "bundleHash": _VECTOR_PLAN_HASH,
            "status": "included",
            "lifecycle": "canonical",
            "generation": 3,
            "payment": {
                "payer": "0x" + "11" * 20,
                "maximumBuilderPayment": "0xe8d4a51000",
                "refundGasPrice": "0x7",
                "maximumRefund": "0x7a120",
                "escrowNonce": "0x2a",
            },
            "submittedAt": 1_700_000_000,
            "updatedAt": None,
            "includedBlockNumber": 42,
            "includedBlockHash": None,
            "transactionHashes": ["0xaaa", "0xbbb"],
            "members": [
                {"txHash": "0xaaa", "index": 0, "role": "payment", "status": "included", "failureReason": None},
                {"txHash": "0xbbb", "index": 1, "role": "bundled", "status": "included", "failureReason": None},
            ],
            "failure": None,
            "ordering": None,
            "error": None,
        }
    }
    actions = BundleActions(mock_w3)
    result = actions.get_bundle_status(_VECTOR_PLAN_HASH)
    assert result.lifecycle == "canonical"
    assert result.generation == 3
    assert result.payment is not None
    assert result.payment.maximum_builder_payment == "0xe8d4a51000"
    assert result.members[0].role == "payment"
