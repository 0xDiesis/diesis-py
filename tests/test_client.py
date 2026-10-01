from unittest.mock import patch

import pytest

from diesis.bundles.actions import BundleActions
from diesis.chains import diesis, diesis_testnet
from diesis.client import DiesisClient
from diesis.exchange.actions import ExchangeActions
from diesis.intents.types import OrderFlags, OrderIntent, SignedOrderIntent
from diesis.patronage.actions import PatronageActions


def test_client_creates_with_rpc_url() -> None:
    with patch("diesis.client.Web3"):
        client = DiesisClient("https://rpc.diesis.xyz")
        assert client.chain == diesis


def test_client_creates_with_testnet() -> None:
    with patch("diesis.client.Web3"):
        client = DiesisClient("https://rpc.testnet.diesis.xyz", chain=diesis_testnet)
        assert client.chain == diesis_testnet


def test_client_has_exchange_namespace() -> None:
    with patch("diesis.client.Web3"):
        client = DiesisClient("https://rpc.diesis.xyz")
        assert isinstance(client.exchange, ExchangeActions)


def test_client_has_bundles_namespace() -> None:
    with patch("diesis.client.Web3"):
        client = DiesisClient("https://rpc.diesis.xyz")
        assert isinstance(client.bundles, BundleActions)


def test_client_does_not_expose_legacy_generic_stealth_bundle_shortcut() -> None:
    with patch("diesis.client.Web3"):
        client = DiesisClient("https://rpc.diesis.xyz")
        assert not hasattr(client, "send_stealth_bundle")


def test_client_has_patronage_namespace() -> None:
    with patch("diesis.client.Web3"):
        client = DiesisClient("https://rpc.diesis.xyz")
        assert isinstance(client.patronage, PatronageActions)


def test_client_get_rules() -> None:
    with patch("diesis.client.Web3") as MockWeb3:
        mock_w3 = MockWeb3.return_value
        mock_w3.provider.make_request.return_value = {"result": {"maxBlockGas": 30_000_000}}
        client = DiesisClient("https://rpc.diesis.xyz")
        client.get_rules()
        assert mock_w3.provider.make_request.call_args[0][0] == "diesis_getRules"


def test_client_get_transaction_status() -> None:
    with patch("diesis.client.Web3") as MockWeb3:
        mock_w3 = MockWeb3.return_value
        mock_w3.provider.make_request.return_value = {"result": {}}
        client = DiesisClient("https://rpc.diesis.xyz")
        client.get_transaction_status("0xabc")
        assert mock_w3.provider.make_request.call_args[0][0] == "diesis_getTransactionStatus"


def test_client_submit_intent_uses_v2_payload_shape() -> None:
    with patch("diesis.client.Web3") as MockWeb3:
        mock_w3 = MockWeb3.return_value
        mock_w3.provider.make_request.return_value = {"result": "0xhash"}
        client = DiesisClient("https://rpc.diesis.xyz")
        intent = SignedOrderIntent(
            intent=OrderIntent(
                trader="0x0000000000000000000000000000000000000001",
                market_id="0x" + "ab" * 32,
                side=0,
                order_type=0,
                price=100,
                amount=50,
                nonce=1,
                trigger_price=0,
                expiry=9999,
                flags=int(OrderFlags.REDUCE_ONLY),
            ),
            signature="0x" + "11" * 65,
            signer="0x0000000000000000000000000000000000000001",
        )

        client.submit_intent(intent)

        method, params = mock_w3.provider.make_request.call_args[0]
        assert method == "diesis_submitIntent"
        payload = params[0]["intent"]
        assert payload["trader"] == intent.intent.trader
        assert payload["triggerPrice"] == "0x0"
        assert payload["flags"] == int(OrderFlags.REDUCE_ONLY)
        assert payload["conductorFeeBps"] == 0
        assert payload["maxConductorFee"] == "0x0"
        assert "reduceOnly" not in payload


def test_client_requires_rpc_url_or_w3() -> None:
    try:
        DiesisClient()
        raise AssertionError("Should raise ValueError")
    except (ValueError, TypeError):
        pass


# Wire fixtures are anchored to core44bed RPC trait and serde response fields.
def test_actual_node_public_wallet_contracts() -> None:
    with patch("diesis.client.Web3") as mock:
        wire = mock.return_value.provider.make_request
        client = DiesisClient("https://rpc.diesis.xyz")
        runtime = {
            "configuredExecutionMode": "parallel",
            "effectiveExecutionMode": "parallel",
            "witnessPolicy": "required",
            "canonicalPass": True,
            "downgradeReason": None,
            "checkpointReplayMode": "checkpoint",
            "blockSequentialFallbackTotal": 0,
        }
        lifecycle = {
            "tx_hash": "0x" + "ab" * 32,
            "status": "published",
            "classification": "canonical",
            "generation": 3,
            "consensus_round": 12,
            "node_received_at": 100,
            "transition_at": 110,
            "lineage": [],
        }
        action = {"status": "native_included", "block_number": 8, "block_hash": "0x" + "cd" * 32, "success": True}
        for method, arguments, rpc_method, result in [
            (client.get_runtime_capabilities, (), "diesis_getRuntimeCapabilities", runtime),
            (client.get_transaction_lifecycle, (lifecycle["tx_hash"],), "diesis_getTransactionLifecycle", lifecycle),
            (client.get_exchange_action_status, ("0x" + "ef" * 32,), "diesis_getExchangeActionStatus", action),
        ]:
            wire.return_value = {"result": result}
            assert method(*arguments) == result
            wire.assert_called_with(rpc_method, list(arguments))
        assert not hasattr(client, "get_pipeline_status")
        assert not hasattr(client, "get_block_witness")
        wire.return_value = {"result": None}
        assert client.get_transaction_lifecycle(lifecycle["tx_hash"]) is None


@pytest.mark.parametrize("value", [-1, True, 1.5, "1", 2**53, 2**64])
def test_node_numeric_parameters_reject_unsafe_wire_values(value: object) -> None:
    with patch("diesis.client.Web3") as mock:
        client = DiesisClient("https://rpc.diesis.xyz")
        for method in (client.get_block_metadata, client.get_consensus_commit_status):
            with pytest.raises(ValueError):
                method(value)
        mock.return_value.provider.make_request.assert_not_called()


def test_node_numeric_parameters_remain_json_numbers() -> None:
    with patch("diesis.client.Web3") as mock:
        client = DiesisClient("https://rpc.diesis.xyz")
        for method, name in [
            (client.get_block_metadata, "diesis_getBlockMetadata"),
            (client.get_consensus_commit_status, "diesis_getConsensusCommitStatus"),
        ]:
            method(2**53 - 1)
            mock.return_value.provider.make_request.assert_called_with(name, [2**53 - 1])


def test_sync_submission_passes_signed_bytes_and_returns_direct_receipt() -> None:
    with patch("diesis.client.Web3") as mock:
        receipt = {
            "transactionHash": "0x" + "ab" * 32,
            "blockHash": "0x" + "cd" * 32,
            "blockNumber": 12,
            "transactionIndex": 0,
            "gasUsed": 21000,
            "effectiveGasPrice": "0x1",
            "status": 1,
            "logs": [],
        }
        mock.return_value.provider.make_request.return_value = {"result": receipt}
        client = DiesisClient("https://rpc.diesis.xyz")
        assert client.send_transaction_sync("0x02AB00") == receipt
        mock.return_value.provider.make_request.assert_called_with("diesis_sendRawTransactionSync", ["0x02AB00"])


@pytest.mark.parametrize("value", ["0x", "0x0", "0xzz", "abcd", {"to": "0xabc"}, None])
def test_sync_submission_rejects_unsigned_or_malformed_input(value: object) -> None:
    with patch("diesis.client.Web3") as mock:
        client = DiesisClient("https://rpc.diesis.xyz")
        with pytest.raises(ValueError):
            client.send_transaction_sync(value)
        mock.return_value.provider.make_request.assert_not_called()
