"""Tests for the diesis.staking.actions module."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from diesis.staking.actions import PositionInfo, StakingActions, ValidatorInfo

# ── Dataclass immutability ───────────────────────────────────────────────────


def test_validator_info_frozen() -> None:
    vi = ValidatorInfo(
        operator="0xabc",
        marks=1,
        bonded=1000,
        joined_checkpoint=1,
        joined_at=100,
        held_at=0,
        held_checkpoint=0,
    )
    with pytest.raises(AttributeError):
        vi.marks = 2  # type: ignore[misc]


def test_position_info_frozen() -> None:
    pi = PositionInfo(validator_id=3, amount=500, entry_checkpoint=10)
    with pytest.raises(AttributeError):
        pi.amount = 999  # type: ignore[misc]


# ── Helpers ──────────────────────────────────────────────────────────────────


def _make_actions() -> tuple[StakingActions, MagicMock]:
    """Return a StakingActions instance wired to a mock contract."""
    mock_w3 = MagicMock()
    mock_contract = MagicMock()
    mock_w3.eth.contract.return_value = mock_contract
    actions = StakingActions(mock_w3)
    return actions, mock_contract


# ── __init__ ─────────────────────────────────────────────────────────────────


def test_init_creates_contract_at_staking_address() -> None:
    from diesis.addresses import DIESIS_STAKING

    mock_w3 = MagicMock()
    mock_w3.eth.contract.return_value = MagicMock()
    StakingActions(mock_w3)

    call_kwargs = mock_w3.eth.contract.call_args
    # address kwarg should resolve to the checksum form of DIESIS_STAKING
    assert call_kwargs is not None
    from web3 import Web3

    assert call_kwargs.kwargs["address"] == Web3.to_checksum_address(DIESIS_STAKING)


# ── Read methods ─────────────────────────────────────────────────────────────


def test_get_validator() -> None:
    actions, mock_contract = _make_actions()
    mock_contract.functions.nodeLedger.return_value.call.return_value = (
        "0xabc",
        1,
        1000,
        2,
        100,
        0,
        0,
    )

    result = actions.get_validator(42)

    assert isinstance(result, ValidatorInfo)
    assert result.operator == "0xabc"
    assert result.marks == 1
    assert result.bonded == 1000
    assert result.joined_checkpoint == 2
    assert result.joined_at == 100
    assert result.held_at == 0
    assert result.held_checkpoint == 0
    mock_contract.functions.nodeLedger.assert_called_once_with(42)
    mock_contract.functions.nodeLedger.return_value.call.assert_called_once()


def test_get_position() -> None:
    actions, mock_contract = _make_actions()
    mock_contract.functions.stakeLots.return_value.call.return_value = (7, 2000, 5)

    result = actions.get_position(99)

    assert isinstance(result, PositionInfo)
    assert result.validator_id == 7
    assert result.amount == 2000
    assert result.entry_checkpoint == 5
    mock_contract.functions.stakeLots.assert_called_once_with(99)
    mock_contract.functions.stakeLots.return_value.call.assert_called_once()


def test_get_unclaimed_rewards() -> None:
    actions, mock_contract = _make_actions()
    mock_contract.functions.unclaimedRewards.return_value.call.return_value = 300

    result = actions.get_unclaimed_rewards(5)

    assert result == 300
    mock_contract.functions.unclaimedRewards.assert_called_once_with(5)
    mock_contract.functions.unclaimedRewards.return_value.call.assert_called_once()


def test_get_aggregate_active_stake() -> None:
    actions, mock_contract = _make_actions()
    mock_contract.functions.aggregateActiveStake.return_value.call.return_value = 5000

    result = actions.get_aggregate_active_stake()

    assert result == 5000
    mock_contract.functions.aggregateActiveStake.assert_called_once_with()
    mock_contract.functions.aggregateActiveStake.return_value.call.assert_called_once()


def test_get_aggregate_stake() -> None:
    actions, mock_contract = _make_actions()
    mock_contract.functions.aggregateStake.return_value.call.return_value = 9000

    result = actions.get_aggregate_stake()

    assert result == 9000
    mock_contract.functions.aggregateStake.assert_called_once_with()
    mock_contract.functions.aggregateStake.return_value.call.assert_called_once()


def test_get_latest_finalized_checkpoint() -> None:
    actions, mock_contract = _make_actions()
    mock_contract.functions.latestFinalizedCheckpoint.return_value.call.return_value = 42

    result = actions.get_latest_finalized_checkpoint()

    assert result == 42
    mock_contract.functions.latestFinalizedCheckpoint.assert_called_once_with()
    mock_contract.functions.latestFinalizedCheckpoint.return_value.call.assert_called_once()


def test_get_circulating_supply() -> None:
    actions, mock_contract = _make_actions()
    mock_contract.functions.circulatingSupply.return_value.call.return_value = 1_000_000

    result = actions.get_circulating_supply()

    assert result == 1_000_000
    mock_contract.functions.circulatingSupply.assert_called_once_with()
    mock_contract.functions.circulatingSupply.return_value.call.assert_called_once()


def test_get_validator_by_address() -> None:
    actions, mock_contract = _make_actions()
    mock_contract.functions.nodeIdByOperator.return_value.call.return_value = 3

    addr = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"
    result = actions.get_validator_by_address(addr)

    assert result == 3
    from web3 import Web3

    mock_contract.functions.nodeIdByOperator.assert_called_once_with(Web3.to_checksum_address(addr))
    mock_contract.functions.nodeIdByOperator.return_value.call.assert_called_once()


def test_is_slashable_true() -> None:
    actions, mock_contract = _make_actions()
    mock_contract.functions.isSlashable.return_value.call.return_value = True

    result = actions.is_slashable(10)

    assert result is True
    mock_contract.functions.isSlashable.assert_called_once_with(10)
    mock_contract.functions.isSlashable.return_value.call.assert_called_once()


def test_is_slashable_false() -> None:
    actions, mock_contract = _make_actions()
    mock_contract.functions.isSlashable.return_value.call.return_value = False

    result = actions.is_slashable(11)

    assert result is False


# ── Write methods ────────────────────────────────────────────────────────────


def test_stake() -> None:
    actions, mock_contract = _make_actions()
    fake_tx = "0xdeadbeef"
    mock_contract.functions.stake.return_value.transact.return_value = fake_tx

    result = actions.stake(validator_id=1, amount=500, **{"from": "0xSender"})

    assert result == fake_tx
    mock_contract.functions.stake.assert_called_once_with(1)
    mock_contract.functions.stake.return_value.transact.assert_called_once_with({"value": 500, "from": "0xSender"})


def test_stake_no_extra_params() -> None:
    actions, mock_contract = _make_actions()
    mock_contract.functions.stake.return_value.transact.return_value = "0x1"

    actions.stake(validator_id=2, amount=100)

    mock_contract.functions.stake.return_value.transact.assert_called_once_with({"value": 100})


def test_request_unstake() -> None:
    actions, mock_contract = _make_actions()
    fake_tx = "0xaabbcc"
    mock_contract.functions.requestUnstake.return_value.transact.return_value = fake_tx

    result = actions.request_unstake(token_id=5, request_id=1, amount=200)

    assert result == fake_tx
    mock_contract.functions.requestUnstake.assert_called_once_with(5, 1, 200)
    mock_contract.functions.requestUnstake.return_value.transact.assert_called_once()


def test_complete_unstake() -> None:
    actions, mock_contract = _make_actions()
    fake_tx = "0xcafe"
    mock_contract.functions.completeUnstake.return_value.transact.return_value = fake_tx

    result = actions.complete_unstake(token_id=5, request_id=1)

    assert result == fake_tx
    mock_contract.functions.completeUnstake.assert_called_once_with(5, 1)
    mock_contract.functions.completeUnstake.return_value.transact.assert_called_once()


def test_harvest_rewards() -> None:
    actions, mock_contract = _make_actions()
    fake_tx = "0xfeed"
    mock_contract.functions.harvestRewards.return_value.transact.return_value = fake_tx

    result = actions.harvest_rewards(token_id=7)

    assert result == fake_tx
    mock_contract.functions.harvestRewards.assert_called_once_with(7)
    mock_contract.functions.harvestRewards.return_value.transact.assert_called_once()


def test_compound_rewards() -> None:
    actions, mock_contract = _make_actions()
    fake_tx = "0xbeef"
    mock_contract.functions.compoundRewards.return_value.transact.return_value = fake_tx

    result = actions.compound_rewards(token_id=8)

    assert result == fake_tx
    mock_contract.functions.compoundRewards.assert_called_once_with(8)
    mock_contract.functions.compoundRewards.return_value.transact.assert_called_once()


def test_register_validator() -> None:
    actions, mock_contract = _make_actions()
    fake_tx = "0x1234"
    mock_contract.functions.registerValidator.return_value.transact.return_value = fake_tx

    pubkey = b"\x02" * 33
    result = actions.register_validator(pubkey=pubkey, self_stake=1000)

    assert result == fake_tx
    mock_contract.functions.registerValidator.assert_called_once_with(pubkey)
    mock_contract.functions.registerValidator.return_value.transact.assert_called_once_with({"value": 1000})


def test_register_validator_with_tx_params() -> None:
    actions, mock_contract = _make_actions()
    mock_contract.functions.registerValidator.return_value.transact.return_value = "0x5"

    pubkey = b"\x03" * 33
    actions.register_validator(pubkey=pubkey, self_stake=500, **{"from": "0xOwner"})

    mock_contract.functions.registerValidator.return_value.transact.assert_called_once_with(
        {"value": 500, "from": "0xOwner"}
    )


def test_set_validator_commission() -> None:
    actions, mock_contract = _make_actions()
    fake_tx = "0xaaaa"
    mock_contract.functions.setValidatorCommission.return_value.transact.return_value = fake_tx

    result = actions.set_validator_commission(validator_id=3, rate=500)

    assert result == fake_tx
    mock_contract.functions.setValidatorCommission.assert_called_once_with(3, 500)
    mock_contract.functions.setValidatorCommission.return_value.transact.assert_called_once()


def test_withdraw_validator() -> None:
    actions, mock_contract = _make_actions()
    fake_tx = "0xbbbb"
    mock_contract.functions.withdrawValidator.return_value.transact.return_value = fake_tx

    result = actions.withdraw_validator(validator_id=4)

    assert result == fake_tx
    mock_contract.functions.withdrawValidator.assert_called_once_with(4)
    mock_contract.functions.withdrawValidator.return_value.transact.assert_called_once()
