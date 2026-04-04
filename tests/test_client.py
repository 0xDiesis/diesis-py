from unittest.mock import MagicMock, patch

from diesis.client import DiesisClient
from diesis.chains import diesis, diesis_testnet
from diesis.exchange.actions import ExchangeActions
from diesis.bundles.actions import BundleActions
from diesis.patronage.actions import PatronageActions


def test_client_creates_with_rpc_url() -> None:
    with patch("diesis.client.Web3") as MockWeb3:
        client = DiesisClient("https://rpc.diesis.xyz")
        assert client.chain == diesis


def test_client_creates_with_testnet() -> None:
    with patch("diesis.client.Web3") as MockWeb3:
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


def test_client_requires_rpc_url_or_w3() -> None:
    try:
        DiesisClient()
        raise AssertionError("Should raise ValueError")
    except (ValueError, TypeError):
        pass
