from typing import Any

import pytest
from eth_abi import encode
from web3 import Web3

from diesis.names import name_service_contracts
from diesis.names_read import read_native_name

HASH = "0x" + "ab" * 32
GENESIS = "0x" + "cd" * 32
OWNER = "0x" + "11" * 20
RECIPIENT = "0x" + "22" * 20
ZERO = "0x" + "00" * 20


class Fixture:
    def __init__(self, **overrides: Any):
        self.overrides = overrides
        self.calls: list[tuple[str, list[Any]]] = []
        self.headers = 0

    async def identity(self) -> str:
        return "configured-rpc-v1"

    async def request(self, method: str, params: list[Any], *, timeout: float, max_response_bytes: int) -> Any:
        self.calls.append((method, params))
        assert 0 < timeout <= 15
        if method == "eth_chainId":
            return "0x7bc"
        if method == "eth_getBlockByNumber":
            if params[0] == "0x0":
                return {"number": "0x0", "hash": GENESIS, "timestamp": "0x0"}
            self.headers += 1
            return {
                "number": "0xa",
                "hash": GENESIS if self.overrides.get("reorg") and self.headers > 1 else HASH,
                "timestamp": "0x64",
            }
        assert params[1] == {"blockHash": HASH, "requireCanonical": True}
        if method == "eth_getCode":
            return self.overrides.get("code", "0x01")
        values = {
            "owner": OWNER,
            "resolver": name_service_contracts["resolver"],
            "expiry": 100,
            "ownershipEpoch": 7,
            "registry": name_service_contracts["registry"],
            "addr": RECIPIENT,
            **self.overrides,
        }
        for fn, value in values.items():
            signature = fn + ("()" if fn == "registry" else "(bytes32)")
            if params[0]["data"][:10] == Web3.to_hex(Web3.keccak(text=signature)[:4]):
                return (
                    "0x"
                    + encode(
                        ["address" if fn in ["owner", "resolver", "registry", "addr"] else "uint256"], [value]
                    ).hex()
                )
        raise ValueError("unexpected selector")


@pytest.mark.asyncio
async def test_observation_owner_recipient_and_expiry_equality() -> None:
    fixture = Fixture()
    result = await read_native_name(
        fixture,
        chain_id=1980,
        input_name="Alice.ds",
        expected_genesis_hash=GENESIS,
        expected_rpc_identity="configured-rpc-v1",
    )
    assert result["status"] == "active"
    assert result["owner"] == OWNER
    assert result["recipient"] == {"status": "resolved", "address": RECIPIENT}
    assert result["ownershipEpoch"] == "7"
    assert result["anchor"] == {"blockNumber": "10", "blockHash": HASH, "timestamp": "100"}
    assert len([c for c in fixture.calls if c[0] == "eth_call"]) == 6


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "overrides,status,recipient_status",
    [
        ({"expiry": 99}, "expired", "resolved"),
        ({"owner": ZERO}, "not-registered", "not-set"),
        ({"resolver": ZERO}, "active", "no-resolver"),
        ({"resolver": RECIPIENT}, "active", "unsupported-resolver"),
        ({"addr": ZERO}, "active", "not-set"),
    ],
)
async def test_states(overrides: dict[str, Any], status: str, recipient_status: str) -> None:
    result = await read_native_name(Fixture(**overrides), chain_id=1980, input_name="alice.ds")
    assert result["status"] == status
    assert result["recipient"]["status"] == recipient_status


@pytest.mark.asyncio
@pytest.mark.parametrize("overrides", [{"reorg": True}, {"code": "0x"}, {"registry": RECIPIENT}])
async def test_failed_evidence(overrides: dict[str, Any]) -> None:
    with pytest.raises(ValueError):
        await read_native_name(Fixture(**overrides), chain_id=1980, input_name="alice.ds")


@pytest.mark.asyncio
@pytest.mark.parametrize("name", ["alice.eth", "alice.xyz", "alice", "alïce.ds"])
async def test_name_isolation(name: str) -> None:
    fixture = Fixture()
    with pytest.raises(ValueError):
        await read_native_name(fixture, chain_id=1980, input_name=name)
    assert fixture.calls == []


@pytest.mark.asyncio
async def test_identity_and_genesis_mismatch() -> None:
    with pytest.raises(ValueError, match="network"):
        await read_native_name(Fixture(), chain_id=19803, input_name="alice.ds")
    with pytest.raises(ValueError, match="Genesis"):
        await read_native_name(Fixture(), chain_id=1980, input_name="alice.ds", expected_genesis_hash=HASH)
    with pytest.raises(ValueError, match="identity"):
        await read_native_name(Fixture(), chain_id=1980, input_name="alice.ds", expected_rpc_identity="other")


@pytest.mark.asyncio
async def test_bounds_retirement_and_canonical_unavailable() -> None:
    import asyncio

    class Stalled(Fixture):
        async def request(self, *args: Any, **kwargs: Any) -> Any:
            await asyncio.Event().wait()

    with pytest.raises(ValueError, match="deadline"):
        await read_native_name(Stalled(), chain_id=1980, input_name="alice.ds", timeout=0.005)
    with pytest.raises(ValueError, match="retired"):
        await read_native_name(Fixture(), chain_id=1980, input_name="alice.ds", current=lambda: False)
    with pytest.raises(ValueError, match="limit"):
        await read_native_name(Fixture(), chain_id=1980, input_name="alice.ds", max_response_bytes=16)

    class Unsupported(Fixture):
        async def request(self, method: str, params: list[Any], *, timeout: float, max_response_bytes: int) -> Any:
            if method == "eth_call":
                raise RuntimeError("canonical selector unsupported")
            return await super().request(method, params, timeout=timeout, max_response_bytes=max_response_bytes)

    fixture = Unsupported()
    with pytest.raises(ValueError):
        await read_native_name(fixture, chain_id=1980, input_name="alice.ds")
    assert len([c for c in fixture.calls if c == ("eth_getBlockByNumber", ["latest", False])]) == 1


@pytest.mark.asyncio
async def test_changed_timestamp_malformed_address_padding_and_retired_response() -> None:
    class Drift(Fixture):
        async def request(self, method: str, params: list[Any], *, timeout: float, max_response_bytes: int) -> Any:
            result = await super().request(method, params, timeout=timeout, max_response_bytes=max_response_bytes)
            if method == "eth_getBlockByNumber" and params[0] == "0xa":
                return {**result, "timestamp": "0x65"}
            return result

    with pytest.raises(ValueError, match="anchor"):
        await read_native_name(Drift(), chain_id=1980, input_name="alice.ds")

    class Dirty(Fixture):
        async def request(self, method: str, params: list[Any], *, timeout: float, max_response_bytes: int) -> Any:
            if method == "eth_call" and params[0]["data"][:10] == Web3.to_hex(Web3.keccak(text="owner(bytes32)")[:4]):
                return "0x" + "ff" * 32
            return await super().request(method, params, timeout=timeout, max_response_bytes=max_response_bytes)

    with pytest.raises(ValueError):
        await read_native_name(Dirty(), chain_id=1980, input_name="alice.ds")
