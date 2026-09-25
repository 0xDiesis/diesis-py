"""Bundle escrow reservation calldata.

The bundle payment transaction must *be* the ``reserveBundle`` call whose
committed terms exactly equal the plan and whose native value equals
``maximum_builder_payment + maximum_refund``. This helper builds that calldata
from the committed plan so a client cannot accidentally under-fund or mis-bind
the reservation.
"""

from __future__ import annotations

from eth_abi.abi import encode as abi_encode
from web3 import Web3

from .plan import plan_hash
from .types import BundlePlan

RESERVE_BUNDLE_SIGNATURE = "reserveBundle(bytes32,uint256,uint256,uint256,uint256,uint64)"


def encode_reserve_bundle(plan: BundlePlan) -> str:
    """Return the ``reserveBundle`` calldata (0x hex) for a committed plan."""
    payment = plan.payment
    selector = bytes(Web3.keccak(text=RESERVE_BUNDLE_SIGNATURE)[:4])
    args = abi_encode(
        ["bytes32", "uint256", "uint256", "uint256", "uint256", "uint64"],
        [
            bytes.fromhex(plan_hash(plan)[2:]),
            payment.maximum_builder_payment,
            payment.refund_gas_price,
            payment.maximum_refund,
            payment.escrow_nonce,
            plan.expiry,
        ],
    )
    return "0x" + (selector + args).hex()


def reservation_value(plan: BundlePlan) -> int:
    """Native wei the reservation transaction must carry."""
    return plan.payment.maximum_builder_payment + plan.payment.maximum_refund
