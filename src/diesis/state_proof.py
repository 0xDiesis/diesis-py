"""MPT state proofs from ``diesis_getStateProof`` and their local verification."""

from __future__ import annotations

import json
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from eth_utils.crypto import keccak

STATE_PROOF_SCHEMA_VERSION = 2
MAX_STATE_PROOF_STORAGE_KEYS = 32

EMPTY_ROOT_HASH = "0x56e81f171bcc55a6ff8345e692c0f86e5b48e01b996cadc001622fb5e363b421"
EMPTY_CODE_HASH = "0xc5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470"
# One branch per key nibble plus a terminal node; each node fits within 1 KiB.
_MAX_PROOF_NODES = 65
_MAX_PROOF_NODE_BYTES = 1024
_MAX_RESPONSE_BYTES = 2 * 1024 * 1024
_MAX_UINT64 = (1 << 64) - 1

_ADDRESS = re.compile(r"0x[0-9a-fA-F]{40}")
_WORD = re.compile(r"0x[0-9a-fA-F]{64}")
_BYTES = re.compile(r"0x(?:[0-9a-fA-F]{2})+")
_QUANTITY = re.compile(r"0x(?:0|[1-9a-fA-F][0-9a-fA-F]{0,63})")
_STORAGE_KEY = re.compile(r"0x[0-9a-fA-F]{1,64}")


class StateProofError(ValueError):
    """A state proof response is malformed or fails verification."""


@dataclass(frozen=True)
class ProvenAccount:
    nonce: int
    balance: int
    code_hash: str
    storage_root: str


@dataclass(frozen=True)
class ProvenSlot:
    slot: str
    value: int


@dataclass(frozen=True)
class VerifiedStateProof:
    """Account and storage values authenticated against a trusted block hash."""

    block_number: int
    block_hash: str
    state_root: str
    timestamp: int
    address: str
    #: ``None`` when the proof shows the account does not exist.
    account: ProvenAccount | None
    #: Requested slots in request order. Proven absence is zero.
    storage: tuple[ProvenSlot, ...]


def _matches(value: object, pattern: re.Pattern[str]) -> bool:
    return isinstance(value, str) and pattern.fullmatch(value) is not None


def state_proof_request(block_number: int, address: str, storage_keys: Sequence[str] = ()) -> dict[str, Any]:
    """Validate a selection and encode the node's request object."""
    if isinstance(block_number, bool) or not isinstance(block_number, int) or not 0 <= block_number <= _MAX_UINT64:
        raise StateProofError("State proof height must be a uint64")
    if not _matches(address, _ADDRESS):
        raise StateProofError("Invalid state proof address")
    keys = list(storage_keys)
    if (
        isinstance(storage_keys, str)
        or len(keys) > MAX_STATE_PROOF_STORAGE_KEYS
        or not all(_matches(key, _WORD) for key in keys)
        or len({key.lower() for key in keys}) != len(keys)
    ):
        raise StateProofError("Expected up to 32 distinct 32-byte storage keys")
    return {"blockNumber": hex(block_number), "address": address, "storageKeys": keys}


def _is_path(value: object) -> bool:
    return (
        isinstance(value, list)
        and len(value) <= _MAX_PROOF_NODES
        and all(_matches(node, _BYTES) and len(node) <= 2 + 2 * _MAX_PROOF_NODE_BYTES for node in value)
    )


def parse_state_proof(value: object, request: Mapping[str, Any]) -> dict[str, Any]:
    """Check the response shape and that it answers ``request``.

    This authenticates nothing; call :func:`verify_state_proof` before using values.
    """
    keys = request["storageKeys"]
    if (
        not isinstance(value, dict)
        or value.get("schemaVersion") != STATE_PROOF_SCHEMA_VERSION
        or type(value.get("schemaVersion")) is not int
        or set(value) != {"schemaVersion", "blockHash", "stateRoot", "canonicalHeader", "checkpoint", "proof"}
    ):
        raise StateProofError("Expected a schemaVersion 2 MPT state proof")
    proof = value["proof"]
    if (
        not _matches(value["blockHash"], _WORD)
        or not _matches(value["stateRoot"], _WORD)
        or not _matches(value["canonicalHeader"], _BYTES)
        or not _matches(value["checkpoint"], _BYTES)
        or not value["checkpoint"].lower().startswith("0x4d505137")
        or not isinstance(proof, dict)
        or set(proof) != {"address", "nonce", "balance", "codeHash", "storageHash", "accountProof", "storageProof"}
        or not _matches(proof["address"], _ADDRESS)
        or proof["address"].lower() != request["address"].lower()
        or not _matches(proof["nonce"], _QUANTITY)
        or int(proof["nonce"], 16) > _MAX_UINT64
        or not _matches(proof["balance"], _QUANTITY)
        or not _matches(proof["codeHash"], _WORD)
        or not _matches(proof["storageHash"], _WORD)
        or not _is_path(proof["accountProof"])
        or not isinstance(proof["storageProof"], list)
        or len(proof["storageProof"]) != len(keys)
    ):
        raise StateProofError("Invalid MPT state proof response")
    for entry, slot in zip(proof["storageProof"], keys, strict=True):
        if (
            not isinstance(entry, dict)
            or set(entry) != {"key", "value", "proof"}
            or not _matches(entry["key"], _STORAGE_KEY)
            or int(entry["key"], 16) != int(slot, 16)
            or not _matches(entry["value"], _QUANTITY)
            or not _is_path(entry["proof"])
        ):
            raise StateProofError("Invalid or out-of-order MPT storage proof")
    if len(json.dumps(value, separators=(",", ":")).encode()) > _MAX_RESPONSE_BYTES:
        raise StateProofError("State proof exceeds the response limit")
    return value


def verify_state_proof(
    response: object,
    *,
    block_number: int,
    address: str,
    storage_keys: Sequence[str] = (),
    trusted_block_hash: str,
) -> VerifiedStateProof:
    """Authenticate the header, account and requested slots against ``trusted_block_hash``.

    Obtain the block hash from a source you already trust, such as a finalized
    header you follow or a certificate verified with ``diesis-state-proof-verify
    --mpt-trust-anchor``. This function does not check the quorum signatures in
    ``checkpoint``, so a hash copied from the same response proves nothing.
    """
    request = state_proof_request(block_number, address, storage_keys)
    value = parse_state_proof(response, request)
    if not _matches(trusted_block_hash, _WORD):
        raise StateProofError("A trusted 32-byte block hash is required")
    header_bytes = bytes.fromhex(value["canonicalHeader"][2:])
    state_root, number, timestamp = _decode_header(header_bytes)
    if (
        "0x" + keccak(header_bytes).hex() != trusted_block_hash.lower()
        or value["blockHash"].lower() != trusted_block_hash.lower()
        or number != block_number
        or state_root != value["stateRoot"].lower()
    ):
        raise StateProofError("Canonical header differs from the trusted block")
    proof = value["proof"]
    leaf = _verify_path(state_root, _nibbles(keccak(hexstr=request["address"])), _nodes(proof["accountProof"]))
    account = None if leaf is None else _decode_account(leaf)
    fields = account or ProvenAccount(0, 0, EMPTY_CODE_HASH, EMPTY_ROOT_HASH)
    if (
        fields.nonce != int(proof["nonce"], 16)
        or fields.balance != int(proof["balance"], 16)
        or fields.storage_root != proof["storageHash"].lower()
        or fields.code_hash != proof["codeHash"].lower()
    ):
        raise StateProofError("MPT account fields differ from the proven account")
    storage = []
    for slot, entry in zip(request["storageKeys"], proof["storageProof"], strict=True):
        encoded = _verify_path(fields.storage_root, _nibbles(keccak(hexstr=slot)), _nodes(entry["proof"]))
        proven = 0 if encoded is None else _decode_storage(encoded)
        if proven != int(entry["value"], 16):
            raise StateProofError("MPT storage value differs from the proven slot")
        storage.append(ProvenSlot(slot, proven))
    return VerifiedStateProof(
        block_number=number,
        block_hash=trusted_block_hash,
        state_root=state_root,
        timestamp=timestamp,
        address=request["address"],
        account=account,
        storage=tuple(storage),
    )


# --- Canonical RLP ---------------------------------------------------------


@dataclass(frozen=True)
class _Item:
    is_list: bool
    payload: bytes  # string payload, or the whole encoding for a list
    raw: bytes


def _invalid() -> StateProofError:
    return StateProofError("Invalid MPT proof encoding")


def _read_length(data: bytes, start: int, size: int) -> int:
    if size > 4 or start + size > len(data) or data[start] == 0:
        raise _invalid()
    length = int.from_bytes(data[start : start + size], "big")
    if length < 56:
        raise _invalid()
    return length


def _rlp_item(data: bytes, offset: int) -> tuple[_Item, int]:
    if offset >= len(data):
        raise _invalid()
    prefix = data[offset]
    is_list = False
    if prefix < 0x80:
        start, length = offset, 1
    elif prefix <= 0xB7:
        start, length = offset + 1, prefix - 0x80
        if length == 1 and (start >= len(data) or data[start] < 0x80):
            raise _invalid()
    elif prefix <= 0xBF:
        length = _read_length(data, offset + 1, prefix - 0xB7)
        start = offset + 1 + prefix - 0xB7
    elif prefix <= 0xF7:
        is_list, start, length = True, offset + 1, prefix - 0xC0
    else:
        is_list = True
        length = _read_length(data, offset + 1, prefix - 0xF7)
        start = offset + 1 + prefix - 0xF7
    end = start + length
    if end > len(data):
        raise _invalid()
    raw = data[offset:end]
    return _Item(is_list, raw if is_list else data[start:end], raw), end


def _rlp_list(data: bytes) -> list[_Item]:
    outer, end = _rlp_item(data, 0)
    if not outer.is_list or end != len(data):
        raise _invalid()
    offset = 1 if data[0] <= 0xF7 else 1 + data[0] - 0xF7
    items = []
    while offset < end:
        item, offset = _rlp_item(data, offset)
        items.append(item)
    return items


def _rlp_string(item: _Item) -> bytes:
    if item.is_list:
        raise _invalid()
    return item.payload


def _rlp_integer(item: _Item, max_bytes: int) -> int:
    data = _rlp_string(item)
    if len(data) > max_bytes or (data and data[0] == 0):
        raise _invalid()
    return int.from_bytes(data, "big")


def _rlp_word(item: _Item) -> str:
    data = _rlp_string(item)
    if len(data) != 32:
        raise _invalid()
    return "0x" + data.hex()


def _decode_header(data: bytes) -> tuple[str, int, int]:
    fields = _rlp_list(data)
    # Pre-London headers have 15 fields; later forks append fields.
    if len(fields) < 15:
        raise _invalid()
    return _rlp_word(fields[3]), _rlp_integer(fields[8], 8), _rlp_integer(fields[11], 8)


def _decode_account(encoded: bytes) -> ProvenAccount:
    fields = _rlp_list(encoded)
    if len(fields) != 4:
        raise StateProofError("Invalid MPT account encoding")
    return ProvenAccount(
        nonce=_rlp_integer(fields[0], 8),
        balance=_rlp_integer(fields[1], 32),
        storage_root=_rlp_word(fields[2]),
        code_hash=_rlp_word(fields[3]),
    )


def _decode_storage(encoded: bytes) -> int:
    item, end = _rlp_item(encoded, 0)
    if end != len(encoded):
        raise _invalid()
    value = _rlp_integer(item, 32)
    if value == 0:
        raise StateProofError("Invalid MPT storage encoding")
    return value


# --- Merkle Patricia path --------------------------------------------------


def _nodes(path: list[str]) -> list[bytes]:
    return [bytes.fromhex(node[2:]) for node in path]


def _nibbles(data: bytes) -> list[int]:
    return [n for byte in data for n in (byte >> 4, byte & 0x0F)]


def _decode_path(item: _Item) -> tuple[bool, list[int]]:
    data = _rlp_string(item)
    if not data:
        raise _invalid()
    flag = data[0]
    odd = bool(flag & 0x10)
    padding = flag & 0x0F
    length = (len(data) - 1) * 2 + int(odd)
    if flag >= 0x40 or (not odd and padding != 0) or length >= _MAX_PROOF_NODES:
        raise _invalid()
    packed = _nibbles(data[1:])
    return bool(flag & 0x20), [padding, *packed] if odd else packed


def _child_reference(item: _Item) -> tuple[str, bytes]:
    raw = item.raw
    if raw[0] == 0xA0 and len(raw) == 33:
        return "hash", raw[1:]
    if 0xC0 <= raw[0] <= 0xDE and len(raw) < 32:
        return "inline", raw
    raise _invalid()


def _is_empty(item: _Item) -> bool:
    return item.raw == b"\x80"


def _bad_path() -> StateProofError:
    return StateProofError("Invalid MPT proof path")


def _verify_path(root: str, key: list[int], nodes: list[bytes]) -> bytes | None:
    """Follow ``key`` from ``root`` through ``nodes`` (root first, then hashed descendants).

    Return the leaf value, or ``None`` for proven absence. The path must end at a
    leaf or a missing child, with no extra nodes.
    """
    if len(nodes) > _MAX_PROOF_NODES or any(len(node) > _MAX_PROOF_NODE_BYTES for node in nodes):
        raise StateProofError("MPT proof exceeds its node budget")
    if root == EMPTY_ROOT_HASH:
        if not nodes or nodes == [b"\x80"]:
            return None
        raise _bad_path()
    if not nodes or "0x" + keccak(nodes[0]).hex() != root:
        raise _bad_path()
    encoded = nodes[0]
    position = 1
    follows_extension = False
    while True:
        fields = _rlp_list(encoded)
        if len(fields) == 2 and not follows_extension:
            is_leaf, path = _decode_path(fields[0])
            if is_leaf:
                data = _rlp_string(fields[1])
                if len(path) != len(key) or not data:
                    raise _bad_path()
                value = data if key == path else None
                break
            if not path or len(path) >= len(key):
                raise _bad_path()
            child = _child_reference(fields[1])
            if key[: len(path)] != path:
                value = None
                break
            key = key[len(path) :]
            follows_extension = True
        elif len(fields) == 17 and _is_empty(fields[16]):
            if not key:
                raise _bad_path()
            occupied = 0
            selected = None
            for index, item in enumerate(fields[:16]):
                if _is_empty(item):
                    continue
                reference = _child_reference(item)
                occupied += 1
                if index == key[0]:
                    selected = reference
            if occupied < 2:
                raise _bad_path()
            if selected is None:
                value = None
                break
            child = selected
            key = key[1:]
            follows_extension = False
        else:
            raise _bad_path()
        kind, reference_bytes = child
        if kind == "inline":
            if position < len(nodes) and nodes[position] == reference_bytes:
                position += 1
            encoded = reference_bytes
        else:
            if position >= len(nodes):
                raise _bad_path()
            candidate = nodes[position]
            position += 1
            if len(candidate) < 32 or keccak(candidate) != reference_bytes:
                raise _bad_path()
            encoded = candidate
    if position != len(nodes):
        raise _bad_path()
    return value
