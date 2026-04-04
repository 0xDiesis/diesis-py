"""Chain definitions for Diesis networks."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class NativeCurrency:
    """Native currency metadata for a chain."""

    name: str
    symbol: str
    decimals: int


@dataclass(frozen=True)
class Chain:
    """Immutable chain configuration."""

    id: int
    name: str
    native_currency: NativeCurrency
    rpc_url: str
    block_explorer_url: str
    testnet: bool = False


diesis = Chain(
    id=1980,
    name="Diesis",
    native_currency=NativeCurrency(name="DS", symbol="DS", decimals=18),
    rpc_url="https://rpc.diesis.xyz",
    block_explorer_url="https://explorer.diesis.xyz",
)

diesis_testnet = Chain(
    id=19803,
    name="Diesis Testnet",
    native_currency=NativeCurrency(name="DS", symbol="DS", decimals=18),
    rpc_url="https://rpc.testnet.diesis.xyz",
    block_explorer_url="https://explorer.testnet.diesis.xyz",
    testnet=True,
)
