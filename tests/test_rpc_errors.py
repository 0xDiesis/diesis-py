import pytest

from diesis.rpc_errors import RpcError, decode_signed_action_error

DATA = {
    "version": 1,
    "kind": "signed-action-error",
    "reason": "exchange_principal_capacity",
    "retryable": False,
    "admission": "unknown",
}


def test_structured_exception_and_decoder() -> None:
    raw = {"code": -32016, "message": "diagnostic", "data": DATA}
    error = RpcError(raw)
    assert error.error is raw
    assert error.code == -32016
    assert error.data is DATA
    decoded = decode_signed_action_error(error)
    assert decoded["status"] == "known"
    assert decoded["reason"] == "exchange_principal_capacity"
    assert decoded["retryable"] is False
    assert decoded["admission"] == "unknown"


@pytest.mark.parametrize(
    "data",
    [
        None,
        {**DATA, "version": 2},
        {**DATA, "reason": "future"},
        {**DATA, "retryable": True},
        {**DATA, "admission": "not-admitted"},
        {**DATA, "extra": True},
    ],
)
def test_unknown_preserves_data(data: object) -> None:
    raw = {"code": -32016, "message": "retry safely", "data": data}
    result = decode_signed_action_error(raw)
    assert result["status"] == "unknown"
    assert result["original"] is raw
    assert result["data"] is data
    assert result["retryable"] is False


def test_transport_error_is_unknown() -> None:
    error = TimeoutError("retry safely")
    assert decode_signed_action_error(error)["status"] == "unknown"


def test_mismatched_code_cycles_and_wrapped_causes() -> None:
    raw = {"code": -32017, "message": "opaque", "data": DATA}
    assert decode_signed_action_error(raw)["status"] == "unknown"
    cycle: dict[str, object] = {}
    cycle["cause"] = cycle
    assert decode_signed_action_error(cycle)["status"] == "unknown"
    cause = RpcError({"code": -32016, "message": "opaque", "data": DATA})
    wrapped = RuntimeError("wrapper")
    wrapped.__cause__ = cause
    # Exception cause chains retain the original even when a typed RPC exception is nested.
    assert decode_signed_action_error(wrapped)["original"] is wrapped
    assert decode_signed_action_error(wrapped)["status"] == "known"
