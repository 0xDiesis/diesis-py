from unittest.mock import MagicMock

from diesis.patronage.actions import GasGrant, PatronageActions


def test_gas_grant_frozen() -> None:
    grant = GasGrant(
        grant_id="0x" + "ab" * 32,
        balance=1000,
        total_contributed=2000,
        total_spent=1000,
        paused=False,
    )
    assert grant.balance == 1000
    try:
        grant.balance = 2000
        raise AssertionError("Should be frozen")
    except AttributeError:
        pass


def test_get_grant_rpc() -> None:
    mock_w3 = MagicMock()
    mock_w3.provider.make_request.return_value = {
        "result": {
            "grantId": "0x" + "ff" * 32,
            "balance": "0x3e8",
            "totalContributed": "0x3e8",
            "totalSpent": "0x0",
            "paused": False,
        }
    }
    actions = PatronageActions(mock_w3)
    actions.get_grant("0x" + "ff" * 32)
    call_args = mock_w3.provider.make_request.call_args
    assert call_args[0][0] == "diesis_getGrant"
    assert call_args[0][1] == ["0x" + "ff" * 32]
