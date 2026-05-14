from unittest.mock import MagicMock

from diesis.bundles.actions import BundleActions
from diesis.bundles.types import BUNDLE_ONLY_SENTINEL, ExecutionFlags, PreparedBundle


def test_execution_flags_values() -> None:
    assert ExecutionFlags.STOP_ON_SUCCESS == 0x01
    assert ExecutionFlags.TOLERATE_INVALID == 0x02
    assert ExecutionFlags.HALT_ON_INVALID == 0x04
    assert ExecutionFlags.PARTIAL_REFUND == 0x08


def test_bundle_only_sentinel() -> None:
    assert BUNDLE_ONLY_SENTINEL == "0x000000000000000000000000000000000A70B1C0"


def test_prepared_bundle_frozen() -> None:
    pb = PreparedBundle(plan_hash="0xabc", version=1)
    assert pb.plan_hash == "0xabc"
    try:
        pb.version = 2
        raise AssertionError("Should be frozen")
    except AttributeError:
        pass


def test_bundle_actions_prepare() -> None:
    mock_w3 = MagicMock()
    mock_w3.provider.make_request.return_value = {"result": {"planHash": "0xabc", "version": 1}}
    actions = BundleActions(mock_w3)
    result = actions.prepare_bundle("0xpay", ["0xtx1"], ExecutionFlags.STOP_ON_SUCCESS)
    assert mock_w3.provider.make_request.call_args[0][0] == "diesis_prepareBundle"
    assert result.plan_hash == "0xabc"


def test_bundle_actions_submit() -> None:
    mock_w3 = MagicMock()
    mock_w3.provider.make_request.return_value = {"result": {"planHash": "0xabc", "status": "pending"}}
    actions = BundleActions(mock_w3)
    result = actions.submit_bundle("0xabc", "0xpay", ["0xtx1"], 0)
    assert mock_w3.provider.make_request.call_args[0][0] == "diesis_submitBundle"
    assert result.plan_hash == "0xabc"
    assert result.status == "pending"


def test_bundle_actions_get_status() -> None:
    mock_w3 = MagicMock()
    mock_w3.provider.make_request.return_value = {
        "result": {
            "planHash": "0xabc",
            "bundleHash": "0xabc",
            "status": "included",
            "submittedAt": 1700000000,
            "updatedAt": None,
            "includedBlockNumber": 42,
            "includedBlockHash": None,
            "transactionHashes": ["0xaaa", "0xbbb"],
            "members": [
                {
                    "txHash": "0xaaa",
                    "index": 0,
                    "role": "payment",
                    "status": "included",
                    "failureReason": None,
                },
                {
                    "txHash": "0xbbb",
                    "index": 1,
                    "role": "bundled",
                    "status": "included",
                    "failureReason": None,
                },
            ],
            "failure": None,
            "ordering": None,
            "error": None,
        }
    }
    actions = BundleActions(mock_w3)
    result = actions.get_bundle_status("0xabc")
    assert mock_w3.provider.make_request.call_args[0][0] == "diesis_getBundleStatus"
    assert mock_w3.provider.make_request.call_args[0][1] == [{"planHash": "0xabc"}]
    assert result.bundle_hash == "0xabc"
    assert result.included_block_number == 42
    assert result.members[0].role == "payment"
