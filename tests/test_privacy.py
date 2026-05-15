"""Tests for the diesis.privacy.actions module."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from web3 import Web3

from diesis.addresses import PRIVACY_POOLS, SHIELDED_POOL
from diesis.privacy.actions import PrivacyActions, PrivacyProvider, ShieldedPoolState


def _make_actions() -> tuple[PrivacyActions, MagicMock, MagicMock]:
    mock_w3 = MagicMock()
    shielded_pool = MagicMock()
    privacy_pools = MagicMock()
    mock_w3.eth.contract.side_effect = [shielded_pool, privacy_pools]
    actions = PrivacyActions(mock_w3)
    return actions, shielded_pool, privacy_pools


def test_init_creates_privacy_contracts() -> None:
    mock_w3 = MagicMock()
    mock_w3.eth.contract.side_effect = [MagicMock(), MagicMock()]

    PrivacyActions(mock_w3)

    assert mock_w3.eth.contract.call_args_list[0].kwargs["address"] == Web3.to_checksum_address(SHIELDED_POOL)
    assert mock_w3.eth.contract.call_args_list[1].kwargs["address"] == Web3.to_checksum_address(PRIVACY_POOLS)


def test_shielded_pool_state_frozen() -> None:
    state = ShieldedPoolState(
        denomination=1,
        depth=20,
        max_leaves=1024,
        root_history_size=30,
        bootstrap_owner="0xabc",
        current_root_index=0,
        initialized=True,
        next_index=1,
        root=b"\x01" * 32,
        tree_initialized=True,
        verifier="0xdef",
    )

    with pytest.raises(AttributeError):
        state.next_index = 2  # type: ignore[misc]


def test_privacy_provider_frozen() -> None:
    provider = PrivacyProvider("Provider", True, b"\x02" * 32)

    with pytest.raises(AttributeError):
        provider.name = "Changed"  # type: ignore[misc]


def test_get_shielded_pool_state() -> None:
    actions, shielded_pool, _ = _make_actions()
    shielded_pool.functions.DENOMINATION.return_value.call.return_value = 1
    shielded_pool.functions.DEPTH.return_value.call.return_value = 20
    shielded_pool.functions.MAX_LEAVES.return_value.call.return_value = 1024
    shielded_pool.functions.ROOT_HISTORY_SIZE.return_value.call.return_value = 30
    shielded_pool.functions.bootstrapOwner.return_value.call.return_value = "0xOwner"
    shielded_pool.functions.currentRootIndex.return_value.call.return_value = 3
    shielded_pool.functions.initialized.return_value.call.return_value = True
    shielded_pool.functions.nextIndex.return_value.call.return_value = 4
    shielded_pool.functions.root.return_value.call.return_value = b"\x11" * 32
    shielded_pool.functions.treeInitialized.return_value.call.return_value = True
    shielded_pool.functions.verifierAddr.return_value.call.return_value = "0xVerifier"

    state = actions.get_shielded_pool_state()

    assert state.denomination == 1
    assert state.depth == 20
    assert state.root == b"\x11" * 32
    assert state.verifier == "0xVerifier"
    shielded_pool.functions.root.assert_called_once_with()


def test_is_known_shielded_root() -> None:
    actions, shielded_pool, _ = _make_actions()
    root = b"\x22" * 32
    shielded_pool.functions.isKnownRoot.return_value.call.return_value = True

    assert actions.is_known_shielded_root(root) is True
    shielded_pool.functions.isKnownRoot.assert_called_once_with(root)


def test_is_shielded_nullifier_spent() -> None:
    actions, shielded_pool, _ = _make_actions()
    nullifier = b"\x33" * 32
    shielded_pool.functions.nullifiers.return_value.call.return_value = False

    assert actions.is_shielded_nullifier_spent(nullifier) is False
    shielded_pool.functions.nullifiers.assert_called_once_with(nullifier)


def test_get_privacy_provider() -> None:
    actions, _, privacy_pools = _make_actions()
    provider = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"
    privacy_pools.functions.providers.return_value.call.return_value = ("Provider", True, b"\x44" * 32)

    result = actions.get_privacy_provider(provider)

    assert result == PrivacyProvider("Provider", True, b"\x44" * 32)
    privacy_pools.functions.providers.assert_called_once_with(Web3.to_checksum_address(provider))


def test_deposit_shielded() -> None:
    actions, shielded_pool, _ = _make_actions()
    commitment = b"\x55" * 32
    shielded_pool.functions.deposit.return_value.transact.return_value = b"\xaa" * 32

    result = actions.deposit_shielded(commitment, value=10, from_="0xSender")

    assert result == b"\xaa" * 32
    shielded_pool.functions.deposit.assert_called_once_with(commitment)
    shielded_pool.functions.deposit.return_value.transact.assert_called_once_with({"value": 10, "from": "0xSender"})


def test_withdraw_shielded_defaults_relayer_and_fee() -> None:
    actions, shielded_pool, _ = _make_actions()
    recipient = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"
    shielded_pool.functions.withdraw.return_value.transact.return_value = b"\xbb" * 32

    result = actions.withdraw_shielded(
        proof=b"\x01",
        merkle_root=b"\x66" * 32,
        nullifier_hash=b"\x77" * 32,
        recipient=recipient,
        amount=5,
    )

    assert result == b"\xbb" * 32
    shielded_pool.functions.withdraw.assert_called_once_with(
        b"\x01",
        b"\x66" * 32,
        b"\x77" * 32,
        Web3.to_checksum_address(recipient),
        5,
        Web3.to_checksum_address("0x0000000000000000000000000000000000000000"),
        0,
    )


def test_register_privacy_provider() -> None:
    actions, _, privacy_pools = _make_actions()
    provider = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"
    privacy_pools.functions.registerProvider.return_value.transact.return_value = b"\xcc" * 32

    result = actions.register_privacy_provider(provider, "Provider", from_="0xOwner")

    assert result == b"\xcc" * 32
    privacy_pools.functions.registerProvider.assert_called_once_with(Web3.to_checksum_address(provider), "Provider")
    privacy_pools.functions.registerProvider.return_value.transact.assert_called_once_with({"from": "0xOwner"})
