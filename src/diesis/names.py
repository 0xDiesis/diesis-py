"""Helpers for Diesis ``.ds`` names."""

from typing import Literal, TypedDict

from web3 import Web3

from . import addresses


class NameServiceRecordType(TypedDict):
    id: Literal["address", "text", "contenthash", "route", "payment", "agent", "attestation"]
    name: str
    description: str


class GenesisPrecompileName(TypedDict):
    key: str
    name: str
    group: str
    address: str


name_service_contracts = {
    "registry": addresses.DIESIS_NAME_REGISTRY,
    "registrar": addresses.DIESIS_BASE_REGISTRAR,
    "resolver": addresses.DIESIS_PUBLIC_RESOLVER,
    "reverse_registrar": addresses.DIESIS_REVERSE_REGISTRAR,
    "verifier": addresses.DIESIS_NAME_VERIFIER,
    "policy": addresses.DIESIS_NAME_POLICY,
}

name_service_record_types: list[NameServiceRecordType] = [
    {
        "id": "address",
        "name": "Address",
        "description": "Primary chain address and coin-specific address records.",
    },
    {
        "id": "text",
        "name": "Text",
        "description": "Profile, project, URL, and service metadata.",
    },
    {
        "id": "contenthash",
        "name": "Content Hash",
        "description": "Decentralized content pointer for a name.",
    },
    {
        "id": "route",
        "name": "Route",
        "description": "Typed service routes for apps and agent endpoints.",
    },
    {
        "id": "payment",
        "name": "Payment Route",
        "description": "Named payment instructions for wallets and protocols.",
    },
    {
        "id": "agent",
        "name": "Agent",
        "description": "AI agent identity and capability records.",
    },
    {
        "id": "attestation",
        "name": "Attestation",
        "description": "Signed identity, project, auditor, validator, and agent claims.",
    },
]

genesis_precompile_names: list[GenesisPrecompileName] = [
    {
        "key": "secp256r1",
        "name": "secp256r1.ds",
        "group": "standard-precompile",
        "address": addresses.SECP256R1,
    },
    {
        "key": "poseidon",
        "name": "poseidon.ds",
        "group": "standard-precompile",
        "address": addresses.POSEIDON,
    },
    {
        "key": "ml-dsa",
        "name": "ml-dsa.ds",
        "group": "standard-precompile",
        "address": addresses.ML_DSA,
    },
    {
        "key": "diesis-staking",
        "name": "diesis-staking.ds",
        "group": "staking",
        "address": addresses.DIESIS_STAKING,
    },
    {
        "key": "diesis-patron",
        "name": "diesis-patron.ds",
        "group": "patronage",
        "address": addresses.DIESIS_PATRON,
    },
    {
        "key": "diesis-config",
        "name": "diesis-config.ds",
        "group": "config",
        "address": addresses.DIESIS_CONFIG,
    },
    {
        "key": "diesis-bootstrap-oracle",
        "name": "diesis-bootstrap-oracle.ds",
        "group": "bridge",
        "address": addresses.BOOTSTRAP_ORACLE,
    },
    {
        "key": "diesis-bootstrap-config",
        "name": "diesis-bootstrap-config.ds",
        "group": "bridge",
        "address": addresses.BOOTSTRAP_CONFIG,
    },
    {
        "key": "diesis-state-writer",
        "name": "diesis-state-writer.ds",
        "group": "config",
        "address": addresses.DIESIS_STATE_WRITER,
    },
    {
        "key": "diesis-position",
        "name": "diesis-position.ds",
        "group": "staking",
        "address": addresses.DIESIS_POSITION,
    },
    {
        "key": "diesis-test-usd",
        "name": "diesis-test-usd.ds",
        "group": "token",
        "address": addresses.DIESIS_TEST_USD,
    },
    {
        "key": "diesis-name-registry",
        "name": "diesis-name-registry.ds",
        "group": "names",
        "address": addresses.DIESIS_NAME_REGISTRY,
    },
    {
        "key": "diesis-base-registrar",
        "name": "diesis-base-registrar.ds",
        "group": "names",
        "address": addresses.DIESIS_BASE_REGISTRAR,
    },
    {
        "key": "diesis-public-resolver",
        "name": "diesis-public-resolver.ds",
        "group": "names",
        "address": addresses.DIESIS_PUBLIC_RESOLVER,
    },
    {
        "key": "diesis-reverse-registrar",
        "name": "diesis-reverse-registrar.ds",
        "group": "names",
        "address": addresses.DIESIS_REVERSE_REGISTRAR,
    },
    {
        "key": "diesis-name-verifier",
        "name": "diesis-name-verifier.ds",
        "group": "names",
        "address": addresses.DIESIS_NAME_VERIFIER,
    },
    {
        "key": "diesis-name-policy",
        "name": "diesis-name-policy.ds",
        "group": "names",
        "address": addresses.DIESIS_NAME_POLICY,
    },
    {
        "key": "wrapped-ds",
        "name": "wrapped-ds.ds",
        "group": "token",
        "address": addresses.WRAPPED_DS,
    },
    {
        "key": "liquid-staked-ds",
        "name": "liquid-staked-ds.ds",
        "group": "token",
        "address": addresses.LIQUID_STAKED_DS,
    },
    {
        "key": "diesis-vrf",
        "name": "diesis-vrf.ds",
        "group": "randomness",
        "address": addresses.VRF,
    },
    {
        "key": "diesis-stealth-announcer",
        "name": "diesis-stealth-announcer.ds",
        "group": "privacy",
        "address": addresses.STEALTH_ANNOUNCER,
    },
    {
        "key": "diesis-stealth-registry",
        "name": "diesis-stealth-registry.ds",
        "group": "privacy",
        "address": addresses.STEALTH_REGISTRY,
    },
    {
        "key": "diesis-groth16-verifier",
        "name": "diesis-groth16-verifier.ds",
        "group": "privacy",
        "address": addresses.GROTH16_VERIFIER,
    },
    {
        "key": "diesis-shielded-pool",
        "name": "diesis-shielded-pool.ds",
        "group": "privacy",
        "address": addresses.SHIELDED_POOL,
    },
    {
        "key": "diesis-privacy-pools",
        "name": "diesis-privacy-pools.ds",
        "group": "privacy",
        "address": addresses.PRIVACY_POOLS,
    },
    {
        "key": "diesis-markets",
        "name": "diesis-markets.ds",
        "group": "exchange",
        "address": addresses.DIESIS_MARKETS,
    },
    {
        "key": "diesis-spot-book",
        "name": "diesis-spot-book.ds",
        "group": "exchange",
        "address": addresses.DIESIS_SPOT_BOOK,
    },
    {
        "key": "diesis-perps-book",
        "name": "diesis-perps-book.ds",
        "group": "exchange",
        "address": addresses.DIESIS_PERPS_BOOK,
    },
    {
        "key": "diesis-margin",
        "name": "diesis-margin.ds",
        "group": "exchange",
        "address": addresses.DIESIS_MARGIN,
    },
    {
        "key": "diesis-settlement",
        "name": "diesis-settlement.ds",
        "group": "exchange",
        "address": addresses.DIESIS_SETTLEMENT,
    },
    {
        "key": "diesis-conductors",
        "name": "diesis-conductors.ds",
        "group": "consensus",
        "address": addresses.DIESIS_CONDUCTORS,
    },
    {
        "key": "diesis-core-vault",
        "name": "diesis-core-vault.ds",
        "group": "exchange",
        "address": addresses.DIESIS_CORE_VAULT,
    },
    {
        "key": "diesis-issuance-auction",
        "name": "diesis-issuance-auction.ds",
        "group": "economics",
        "address": addresses.DIESIS_ISSUANCE_AUCTION,
    },
    {
        "key": "diesis-buyback-burn",
        "name": "diesis-buyback-burn.ds",
        "group": "economics",
        "address": addresses.DIESIS_BUYBACK_BURN,
    },
    {
        "key": "diesis-operator-bond",
        "name": "diesis-operator-bond.ds",
        "group": "economics",
        "address": addresses.DIESIS_OPERATOR_BOND,
    },
    {
        "key": "diesis-erc20-factory",
        "name": "diesis-erc20-factory.ds",
        "group": "token",
        "address": addresses.DIESIS_ERC20_FACTORY,
    },
    {
        "key": "diesis-perp-deploy",
        "name": "diesis-perp-deploy.ds",
        "group": "exchange",
        "address": addresses.DIESIS_PERP_DEPLOY,
    },
    {
        "key": "multicall3",
        "name": "multicall3.ds",
        "group": "ecosystem",
        "address": addresses.MULTICALL3,
    },
    {
        "key": "permit2",
        "name": "permit2.ds",
        "group": "ecosystem",
        "address": addresses.PERMIT2,
    },
]

_genesis_precompile_by_name = {entry["name"]: entry for entry in genesis_precompile_names}
_genesis_precompile_by_address = {entry["address"].lower(): entry for entry in genesis_precompile_names}

_DIESIS_NAME_SUFFIX = ".ds"
_MIN_REGISTRAR_LABEL_LENGTH = 3
_MAX_LABEL_LENGTH = 63
_MAX_NAME_LENGTH = 255


def _assert_valid_diesis_label(label: str, *, is_registrar_label: bool) -> None:
    if (
        len(label) == 0
        or len(label) > _MAX_LABEL_LENGTH
        or (is_registrar_label and len(label) < _MIN_REGISTRAR_LABEL_LENGTH)
        or label.startswith("-")
        or label.endswith("-")
        or not label.replace("-", "").isalnum()
        or not label.isascii()
        or not label.lower() == label
    ):
        raise ValueError("Invalid .ds name")


def normalize_diesis_name(input_name: str) -> str:
    """Normalize user input to a canonical lower-case Diesis ``.ds`` name."""
    trimmed = input_name.strip().lower()
    normalized = trimmed if trimmed.endswith(_DIESIS_NAME_SUFFIX) else f"{trimmed}{_DIESIS_NAME_SUFFIX}"

    if len(normalized) > _MAX_NAME_LENGTH:
        raise ValueError("Invalid .ds name")

    name_without_suffix = normalized[: -len(_DIESIS_NAME_SUFFIX)]
    labels = name_without_suffix.split(".")
    registrar_label_index = len(labels) - 1

    for index, label in enumerate(labels):
        _assert_valid_diesis_label(label, is_registrar_label=index == registrar_label_index)

    return normalized


def resolve_genesis_precompile_name(input_name: str) -> GenesisPrecompileName | None:
    """Resolve a canonical genesis precompile ``.ds`` alias, if one exists."""
    return _genesis_precompile_by_name.get(normalize_diesis_name(input_name))


def reverse_resolve_genesis_precompile(address: str) -> GenesisPrecompileName | None:
    """Return the canonical genesis precompile alias for an address, if known."""
    return _genesis_precompile_by_address.get(address.lower())


def diesis_namehash(input_name: str) -> str:
    """Return the ENS-compatible bytes32 node for a Diesis ``.ds`` name."""
    node = b"\x00" * 32
    for label in reversed(normalize_diesis_name(input_name).split(".")):
        node = Web3.keccak(node + Web3.keccak(text=label))
    return Web3.to_hex(node)
