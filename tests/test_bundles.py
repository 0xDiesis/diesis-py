from unittest.mock import MagicMock
from diesis.bundles.types import BUNDLE_ONLY_SENTINEL, BundleResult, ExecutionFlags, PreparedBundle
from diesis.bundles.actions import BundleActions

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
    actions.prepare_bundle("0xpay", ["0xtx1"], ExecutionFlags.STOP_ON_SUCCESS)
    assert mock_w3.provider.make_request.call_args[0][0] == "diesis_prepareBundle"

def test_bundle_actions_submit() -> None:
    mock_w3 = MagicMock()
    mock_w3.provider.make_request.return_value = {"result": {"planHash": "0xabc", "status": "pending"}}
    actions = BundleActions(mock_w3)
    actions.submit_bundle("0xabc", "0xpay", ["0xtx1"], 0)
    assert mock_w3.provider.make_request.call_args[0][0] == "diesis_submitBundle"

def test_bundle_actions_get_status() -> None:
    mock_w3 = MagicMock()
    mock_w3.provider.make_request.return_value = {"result": {"planHash": "0xabc", "status": "included"}}
    actions = BundleActions(mock_w3)
    actions.get_bundle_status("0xabc")
    assert mock_w3.provider.make_request.call_args[0][0] == "diesis_getBundleStatus"
