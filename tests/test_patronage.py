from unittest.mock import MagicMock
from diesis.patronage.actions import PatronageActions, PatronFund

def test_patron_fund_frozen() -> None:
    pf = PatronFund(balance=1000, patron="0xabc", fund_type=1)
    assert pf.balance == 1000
    try:
        pf.balance = 2000
        raise AssertionError("Should be frozen")
    except AttributeError:
        pass

def test_get_patron_fund_rpc() -> None:
    mock_w3 = MagicMock()
    mock_w3.provider.make_request.return_value = {"result": {"balance": "0x3e8", "patron": "0xabc", "fundType": 1}}
    actions = PatronageActions(mock_w3)
    actions.get_patron_fund("0x" + "ff" * 32)
    call_args = mock_w3.provider.make_request.call_args
    assert call_args[0][0] == "diesis_getPatronFund"
    assert call_args[0][1] == ["0x" + "ff" * 32]
