from unittest.mock import MagicMock

import pytest

from diesis._rpc import _rpc


def test_rpc_returns_the_provider_result() -> None:
    w3 = MagicMock()
    w3.provider.make_request.return_value = {"result": {"ready": True}}

    assert _rpc(w3, "diesis_example", ["argument"]) == {"ready": True}
    assert w3.provider.make_request.call_args[0] == ("diesis_example", ["argument"])


def test_rpc_raises_for_provider_errors() -> None:
    w3 = MagicMock()
    w3.provider.make_request.return_value = {"error": {"code": -32000, "message": "failed"}}

    with pytest.raises(RuntimeError, match="RPC error:.*failed"):
        _rpc(w3, "diesis_example", [])
