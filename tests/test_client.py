from unittest.mock import patch

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


def test_client_get_pipeline_status() -> None:
    with patch("diesis.client.Web3") as MockWeb3:
        mock_w3 = MockWeb3.return_value
        mock_w3.provider.make_request.return_value = {"result": {}}
        client = DiesisClient("https://rpc.diesis.xyz")
        client.get_pipeline_status()
        assert mock_w3.provider.make_request.call_args[0][0] == "diesis_getPipelineStatus"


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
