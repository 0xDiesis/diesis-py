"""Run from a clean wheel install, outside the repository."""

import asyncio
import json
import sys
from pathlib import Path

from eth_abi import encode
from web3 import Web3

import diesis
from diesis import decode_signed_action_error, read_native_name
from diesis.abi.generated import DIESISPUBLICRESOLVER_ABI
from diesis.names import name_service_contracts

assert str(Path(diesis.__file__).resolve()).startswith(str(Path(sys.prefix).resolve()))
assert DIESISPUBLICRESOLVER_ABI
HASH = "0x" + "ab" * 32
GENESIS = "0x" + "cd" * 32
OWNER = "0x" + "11" * 20
RECIPIENT = "0x" + "22" * 20


class Fixture:
    requests = 0

    async def identity(self) -> str:
        return "wheel-fixture-v1"

    async def request(self, method, params, *, timeout, max_response_bytes):
        self.requests += 1
        if method == "eth_chainId":
            return "0x7bc"
        if method == "eth_getBlockByNumber":
            return (
                {"number": "0x0", "hash": GENESIS, "timestamp": "0x0"}
                if params[0] == "0x0"
                else {"number": "0xa", "hash": HASH, "timestamp": "0x64"}
            )
        assert params[1] == {"blockHash": HASH, "requireCanonical": True}
        if method == "eth_getCode":
            return "0x01"
        values = {
            "owner": OWNER,
            "resolver": name_service_contracts["resolver"],
            "expiry": 100,
            "ownershipEpoch": 7,
            "registry": name_service_contracts["registry"],
            "addr": RECIPIENT,
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
        raise RuntimeError("Unexpected request")


async def main():
    rpc = Fixture()
    result = await read_native_name(
        rpc,
        chain_id=1980,
        input_name="alice.ds",
        expected_genesis_hash=GENESIS,
        expected_rpc_identity="wheel-fixture-v1",
    )
    assert result["owner"] == OWNER
    assert result["recipient"] == {"status": "resolved", "address": RECIPIENT}
    assert result["status"] == "active"
    decoded = decode_signed_action_error(
        {
            "code": -32017,
            "message": "opaque",
            "data": {
                "version": 1,
                "kind": "signed-action-error",
                "reason": "exchange_submission_outcome_unknown",
                "retryable": False,
                "admission": "unknown",
            },
        }
    )
    assert decoded["status"] == "known"
    print(
        json.dumps(
            {
                "entrypoints": ["root", "names_read", "rpc_errors", "abi"],
                "requests": rpc.requests,
                "sourceImports": False,
                "read": "explicit injected deterministic canonical RPC fixture",
                "networkQualification": False,
            }
        )
    )


asyncio.run(main())
