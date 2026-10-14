"""Portable canonical Names observations. No signing or provider fallback."""

from __future__ import annotations

import asyncio
import json
import re
import time
from collections.abc import Callable, Coroutine
from typing import Any, Literal, Protocol, TypedDict, TypeVar, cast

from eth_abi.abi import decode, encode
from web3 import Web3

from .names import diesis_namehash, name_service_contracts, normalize_diesis_name


class NativeNamesRpc(Protocol):
    """Adapter must enforce timeout, bytes before buffering, and refuse redirects/fallback."""

    async def identity(self) -> str: ...
    async def request(self, method: str, params: list[Any], *, timeout: float, max_response_bytes: int) -> Any: ...


class NameNetwork(TypedDict):
    genesisHash: str
    rpcIdentity: str


class NameAnchor(TypedDict):
    blockNumber: str
    blockHash: str
    timestamp: str


class NameContracts(TypedDict):
    registry: str
    canonicalResolver: str


class NameRecipient(TypedDict, total=False):
    status: Literal["resolved", "no-resolver", "unsupported-resolver", "not-set"]
    address: str


class NativeNameObservationV1(TypedDict):
    version: Literal[1]
    kind: Literal["native-name-observation"]
    name: str
    node: str
    chainId: Literal["ethereum:1980", "ethereum:19803"]
    network: NameNetwork
    anchor: NameAnchor
    contracts: NameContracts
    owner: str
    resolver: str
    expiry: str
    ownershipEpoch: str
    status: Literal["active", "expired", "not-registered"]
    recipient: NameRecipient
    verification: Literal["rpc-observation"]


class NativeNamesReadError(ValueError):
    """Missing, changed, malformed or unavailable observation evidence."""


T = TypeVar("T")
ZERO = "0x" + "0" * 40


def _hash(value: Any) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"0x[0-9a-fA-F]{64}", value):
        raise NativeNamesReadError("Malformed block hash")
    return value.lower()


def _quantity(value: Any, bits: int = 64) -> int:
    if not isinstance(value, str) or not re.fullmatch(r"0x(?:0|[1-9a-fA-F][0-9a-fA-F]*)", value):
        raise NativeNamesReadError("Malformed RPC quantity")
    result = int(value, 16)
    if result >= 1 << bits:
        raise NativeNamesReadError("RPC quantity overflow")
    return result


def _header(value: Any) -> NameAnchor:
    if type(value) is not dict:
        raise NativeNamesReadError("Malformed block header")
    return {
        "blockNumber": str(_quantity(value.get("number"))),
        "blockHash": _hash(value.get("hash")),
        "timestamp": str(_quantity(value.get("timestamp"))),
    }


def _address(value: Any) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"0x[0-9a-fA-F]{40}", value):
        raise NativeNamesReadError("Malformed contract address")
    return value.lower()


def _uint(value: Any, bits: int) -> int:
    if type(value) is not int or value < 0 or value >= 1 << bits:
        raise NativeNamesReadError("Contract integer overflow")
    return value


def _json(value: Any, depth: int = 0) -> None:
    if depth > 64:
        raise NativeNamesReadError("Malformed RPC response")
    if type(value) in (str, int, float, bool, type(None)):
        return
    if type(value) is dict:
        if any(type(key) is not str for key in value):
            raise NativeNamesReadError("Malformed RPC object")
        for item in value.values():
            _json(item, depth + 1)
    elif type(value) is list:
        for item in value:
            _json(item, depth + 1)
    else:
        raise NativeNamesReadError("Malformed RPC response")


async def read_native_name(
    rpc: NativeNamesRpc,
    *,
    chain_id: Literal[1980, 19803],
    input_name: str,
    expected_genesis_hash: str | None = None,
    expected_rpc_identity: str | None = None,
    timeout: float = 15,
    max_response_bytes: int = 262_144,
    current: Callable[[], bool] = lambda: True,
) -> NativeNameObservationV1:
    """Return a numbered canonical RPC observation, without finality or send authority."""
    if not isinstance(input_name, str) or not input_name.isascii() or not input_name.strip().lower().endswith(".ds"):
        raise NativeNamesReadError("Enter an explicit ASCII .ds name")
    name = normalize_diesis_name(input_name)
    if len(name) > 253 or any(ord(c) < 32 or ord(c) > 126 for c in input_name):
        raise NativeNamesReadError("Enter an explicit ASCII .ds name up to 253 characters")
    node = diesis_namehash(name)
    if (
        chain_id not in (1980, 19803)
        or not 0 < timeout <= 15
        or type(max_response_bytes) is not int
        or not 0 < max_response_bytes <= 262_144
    ):
        raise NativeNamesReadError("Invalid native network or read bounds")
    if expected_genesis_hash is not None:
        _hash(expected_genesis_hash)
    if expected_rpc_identity is not None and (not expected_rpc_identity or len(expected_rpc_identity) > 128):
        raise NativeNamesReadError("Invalid expected RPC identity")
    end = time.monotonic() + timeout

    def check() -> float:
        if not current():
            raise NativeNamesReadError("Native name read retired")
        remaining = end - time.monotonic()
        if remaining <= 0:
            raise NativeNamesReadError("Native name read deadline exceeded")
        return remaining

    async def bounded(operation: Callable[[], Coroutine[Any, Any, T]]) -> T:
        remaining = check()
        result = await asyncio.wait_for(operation(), remaining)
        check()
        return result

    async def request(method: str, params: list[Any]) -> Any:
        result = await bounded(
            lambda: rpc.request(method, params, timeout=check(), max_response_bytes=max_response_bytes)
        )
        _json(result)
        if len(json.dumps(result, ensure_ascii=False).encode()) > max_response_bytes:
            raise NativeNamesReadError("Native name response limit exceeded")
        return result

    async def identity() -> str:
        value = await bounded(rpc.identity)
        if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9._:-]{1,128}", value):
            raise NativeNamesReadError("Invalid RPC identity")
        return value

    async def chain() -> None:
        if _quantity(await request("eth_chainId", []), 256) != chain_id:
            raise NativeNamesReadError("Native network mismatch")

    try:
        rpc_identity = await identity()
        if expected_rpc_identity is not None and rpc_identity != expected_rpc_identity:
            raise NativeNamesReadError("RPC identity mismatch")
        await chain()
        genesis = _header(await request("eth_getBlockByNumber", ["0x0", False]))
        if (
            genesis["blockNumber"] != "0"
            or expected_genesis_hash is not None
            and genesis["blockHash"] != expected_genesis_hash.lower()
        ):
            raise NativeNamesReadError("Genesis mismatch")
        anchor = _header(await request("eth_getBlockByNumber", ["latest", False]))
        selector = {"blockHash": anchor["blockHash"], "requireCanonical": True}
        registry = name_service_contracts["registry"].lower()
        canonical_resolver = name_service_contracts["resolver"].lower()

        async def require_code(target: str) -> None:
            code = await request("eth_getCode", [target, selector])
            if not isinstance(code, str) or not re.fullmatch(r"0x(?:[0-9a-fA-F]{2})+", code):
                raise NativeNamesReadError("Native name contract bytecode unavailable")

        async def read(target: str, fn: str, output: str, args: list[bytes]) -> Any:
            signature = fn + ("()" if not args else "(bytes32)")
            data = Web3.to_hex(Web3.keccak(text=signature)[:4]) + encode(["bytes32"] * len(args), args).hex()
            raw = await request("eth_call", [{"to": target, "data": data}, selector])
            if not isinstance(raw, str) or not re.fullmatch(r"0x[0-9a-fA-F]{64}", raw):
                raise NativeNamesReadError("Malformed native name contract reply")
            return decode([output], bytes.fromhex(raw[2:]))[0]

        await require_code(registry)
        node_bytes = bytes.fromhex(node[2:])
        owner_value = _address(await read(registry, "owner", "address", [node_bytes]))
        resolver_value = _address(await read(registry, "resolver", "address", [node_bytes]))
        expiry = _uint(await read(registry, "expiry", "uint64", [node_bytes]), 64)
        epoch = _uint(await read(registry, "ownershipEpoch", "uint256", [node_bytes]), 256)
        owner = None if owner_value == ZERO else owner_value
        resolver = None if resolver_value == ZERO else resolver_value
        status: Literal["active", "expired", "not-registered"] = (
            "not-registered"
            if owner is None
            else "expired"
            if expiry and int(anchor["timestamp"]) > expiry
            else "active"
        )
        recipient: NameRecipient = {
            "status": "no-resolver"
            if resolver is None
            else "unsupported-resolver"
            if resolver != canonical_resolver
            else "not-set"
        }
        if owner is not None:
            if resolver is None:
                recipient = {"status": "no-resolver"}
            elif resolver != canonical_resolver:
                recipient = {"status": "unsupported-resolver"}
            else:
                await require_code(canonical_resolver)
                if _address(await read(canonical_resolver, "registry", "address", [])) != registry:
                    raise NativeNamesReadError("Resolver registry mismatch")
                resolved = _address(await read(canonical_resolver, "addr", "address", [node_bytes]))
                recipient = {"status": "not-set"} if resolved == ZERO else {"status": "resolved", "address": resolved}
        confirmed = _header(await request("eth_getBlockByNumber", [hex(int(anchor["blockNumber"])), False]))
        if confirmed != anchor:
            raise NativeNamesReadError("Native name anchor changed")
        if _header(await request("eth_getBlockByNumber", ["0x0", False])) != genesis:
            raise NativeNamesReadError("Genesis changed")
        await chain()
        if await identity() != rpc_identity:
            raise NativeNamesReadError("RPC identity changed")
        check()
        return {
            "version": 1,
            "kind": "native-name-observation",
            "name": name,
            "node": node,
            "chainId": cast(Literal["ethereum:1980", "ethereum:19803"], f"ethereum:{chain_id}"),
            "network": {"genesisHash": genesis["blockHash"], "rpcIdentity": rpc_identity},
            "anchor": anchor,
            "contracts": {"registry": registry, "canonicalResolver": canonical_resolver},
            "owner": owner_value,
            "resolver": resolver_value,
            "expiry": str(expiry),
            "ownershipEpoch": str(epoch),
            "status": status,
            "recipient": recipient,
            "verification": "rpc-observation",
        }
    except NativeNamesReadError:
        raise
    except TimeoutError as error:
        raise NativeNamesReadError("Native name read deadline exceeded") from error
    except Exception as error:
        check()
        raise NativeNamesReadError("Native name read unavailable") from error
