<div align="center">

<img src="https://github.com/0xDiesis/diesis/raw/main/docs/diesis.png" alt="Diesis" width="120">

<pre>
 ___ ___ ___ ___ ___ ___
|   \_ _| __/ __|_ _/ __|
| |) | || _|\__ \| |\__ \
|___/___|___|___/___|___/
 -  -  -  -  -  -  -  -
</pre>

**The Python SDK for Diesis**

Read the chain's order books, sign gasless orders, bundle transactions, stake
DS, and resolve `.ds` names from Python. Built on
[web3.py](https://web3py.readthedocs.io), so your existing providers and
middleware still work.

Chain ID `1980` · Token **DS** · Runtime **web3.py 7** · Python **3.10+**

*Greek δίεσις: the smallest interval in music.<br>Diesis aims for the smallest interval between blocks.*

</div>

---

## Why this SDK

Diesis builds trading, fee sponsorship, names, staking, and private transfers
into the chain itself. This package gives each of those a typed Python method,
so a trading bot, backend service, or notebook can use them without
hand-encoding calldata or EIP-712 structs.

- One `DiesisClient` exposes `exchange`, `bundles`, `patronage`, `privacy`, and
  `staking`.
- Signing helpers use the same EIP-712 field order and domains as the Rust
  node and the [TypeScript SDK](https://github.com/0xDiesis/diesis-js).
- Inputs are checked before signing. A bad address, a malformed `bytes32`, an
  out-of-range integer, or an unknown order flag raises before a signature
  exists.
- The package passes `mypy --strict`, and ABIs are generated from the Solidity
  sources.

## Install

The package is not on PyPI yet. Install it from GitHub with authenticated Git
access, and pin a commit:

```bash
python -m pip install 'diesis-sdk @ git+https://github.com/0xDiesis/diesis-py.git@<commit>'
```

The distribution is named `diesis-sdk`. You import it as `diesis`.

## Connect

**In short.** You point the client at a Diesis node. Add a private key if you
want to sign things.

**Details.** `DiesisClient` takes an RPC URL or an existing `Web3` instance.
The `chain` argument sets the chain ID used in signing domains, and defaults
to mainnet. The private key stays local and is only used for signing helpers
on the client.

```python
from diesis import DiesisClient, diesis_testnet

client = DiesisClient(
    "https://rpc.testnet.diesis.xyz",
    chain=diesis_testnet,
    private_key="0x...",
)

client.w3.eth.block_number  # plain web3.py still works
```

| Network        | Chain ID | Export           |
| -------------- | -------- | ---------------- |
| Diesis Mainnet | 1980     | `diesis`         |
| Diesis Testnet | 19803    | `diesis_testnet` |

## Read the exchange

**In short.** Diesis runs its order books inside the chain, like a stock
exchange that every node keeps a copy of. You can list markets, see who wants
to buy and sell at what price, and check your balances.

**Details.** These methods call the `exchange_*` RPC methods. `estimate_fill`
walks the current book and reports what a market order of a given size would
get, without placing anything. A market ID is a hash of the base token, quote
token, and market type, so `market_id` computes it offline.

```python
from diesis.exchange.utils import market_id

markets = client.exchange.get_markets()
book = client.exchange.get_order_book(markets[0]["marketId"], depth=20)
account = client.exchange.get_account("0x...")
estimate = client.exchange.estimate_fill(markets[0]["marketId"], side=0, amount=10**18)

spot_id = market_id(base_token, quote_token, market_type=0)
```

`get_market`, `get_trades`, and `get_funding_rates` are also on
`client.exchange`.

## Trade without gas

**In short.** You sign an order with your key, the same way you'd sign a login
message. A relayer pays the fee and puts it on chain for you. Your account
never needs DS for gas.

**Details.** `OrderIntent` is a frozen dataclass with snake_case fields. The
signer serializes it with the canonical Solidity names and field order. The
signing domain's `verifying_contract` must be the book the order goes to, and
it defaults to the spot book. `submit_intent` sends the result to
`diesis_submitIntent`.

```python
import time

from diesis.intents.types import OrderFlags, OrderIntent

intent = OrderIntent(
    trader="0x0000000000000000000000000000000000000001",
    market_id="0x" + "01" * 32,
    side=0,
    order_type=0,
    price=100,
    amount=50,
    nonce=1,
    expiry=int(time.time()) + 3600,
    flags=int(OrderFlags.POST_ONLY),
)

signed = client.sign_order_intent(intent)
intent_hash = client.submit_intent(signed)
```

For a perpetual market, call `diesis.intents.sign_order_intent` directly with
`verifying_contract=addresses.DIESIS_PERPS_BOOK`.
`sign_trading_key_authorization` lets a hot key sign for a main account, up
to an expiry and a notional cap.

## Bundle transactions

**In short.** A bundle is a list of transactions that run in a fixed order as
one plan. Everyone whose transaction is in the list signs off on the whole
plan, and a separate payment covers the builder.

**Details.** Build a `BundlePlanV2`, have each member sign a detached consent,
and submit it with the signed reservation transaction. `plan_hash` and
`sign_member_consent` reproduce the node's digests locally, so you can build
and check a bundle offline. `encode_reserve_bundle_v2` and `reservation_value`
give you the calldata and value for the payer's reservation.
`ExecutionFlags` control rollback. The payment stays committed even when
bundled work rolls back.

```python
import time

from diesis.bundles import (
    BundleManifestEntry,
    BundlePaymentTerms,
    BundlePlanV2,
    ExecutionFlags,
    encode_reserve_bundle_v2,
    reservation_value,
    sign_member_consent,
)

plan = BundlePlanV2(
    chain_id=client.chain.id,
    expiry=int(time.time()) + 60,
    flags=ExecutionFlags.STOP_ON_SUCCESS,
    payment=BundlePaymentTerms(
        payer=payer_address,
        maximum_builder_payment=10**12,
        refund_gas_price=10**9,
        maximum_refund=5 * 10**11,
        escrow_nonce=1,
    ),
    ordered_members=[
        BundleManifestEntry(transaction_hash=member_tx_hash, gas_allowance=250_000),
    ],
)

prepared = client.bundles.prepare_bundle(plan)
consent = sign_member_consent(member_key, plan, member_index=0)

# Payer signs a transaction to the escrow with this data and value.
reserve_data = encode_reserve_bundle_v2(plan)
reserve_value = reservation_value(plan)

result = client.bundles.submit_bundle(
    plan,
    payment=raw_reservation_tx,
    members=[(raw_member_tx, consent)],
)
status = client.bundles.get_bundle_status(prepared.plan_hash)
```

## Sponsor gas

**In short.** An app can put DS into a gas grant, and the chain spends it on
fees for that app's users. New users can start before they own any DS.

**Details.** `client.patronage.get_grant` reads a grant from the Patron system
contract. Campaign owners sign `CampaignVoucherV1` vouchers. Each voucher lets
one beneficiary call one target and one function selector, with caps on
transaction count, lifetime spend, and expiry. The `encode_*` helpers return
calldata for registering campaigns and claiming or revoking vouchers.

```python
from diesis.patronage import (
    CampaignVoucherV1,
    campaign_id_for,
    encode_claim_campaign_voucher,
    sign_campaign_voucher,
)

grant = client.patronage.get_grant("0x...")

voucher = CampaignVoucherV1(
    campaign_id=campaign_id_for(owner_address, salt),
    beneficiary="0x...",
    target="0x...",
    selector="0xa9059cbb",
    max_transactions=5,
    max_lifetime_spend=10**16,
    expiry=int(time.time()) + 86_400,
    nonce=1,
)
signature = sign_campaign_voucher(owner_key, voucher, chain_id=client.chain.id)
calldata = encode_claim_campaign_voucher(voucher, signature)
```

## Stake DS

**In short.** You lock DS with a validator to help secure the chain and earn
rewards. Your stake is a token you hold, and you can claim or restake rewards
whenever you like.

**Details.** `client.staking` wraps the `DiesisStaking` system contract. Each
position is an ERC-721 token. Unstaking takes two calls, `request_unstake` and
then `complete_unstake` after the cooldown. Write methods pass extra keyword
arguments through to web3.py as transaction parameters.

```python
validator = client.staking.get_validator(1)
rewards = client.staking.get_unclaimed_rewards(token_id=42)

client.staking.stake(1, amount=100 * 10**18, **{"from": my_address})
client.staking.compound_rewards(42, **{"from": my_address})
```

## Resolve `.ds` names

**In short.** `.ds` names work like web addresses for accounts. `alice.ds` is
easier to read and share than `0xd1e5...`.

**Details.** `normalize_diesis_name` lowercases and validates a name.
`diesis_namehash` computes the ENS-style node hash the registry and resolver
use. Every system contract has a genesis name, such as
`diesis-spot-book.ds`, and those resolve offline.

```python
from diesis import (
    diesis_namehash,
    normalize_diesis_name,
    resolve_genesis_precompile_name,
)

normalize_diesis_name("Alice.DS")  # 'alice.ds'
diesis_namehash("alice.ds")  # '0x82b9...1b17'
resolve_genesis_precompile_name("diesis-spot-book.ds")["address"]
```

## Private transfers

**In short.** The shielded pool lets you move tokens without showing who paid
whom. A zero-knowledge proof shows the numbers add up without revealing the
details.

**Details.** `client.privacy` reads pool state, known roots, and spent
nullifiers, and sends deposit, transfer, and withdrawal transactions. Proof
generation is not in the Python SDK. Produce proofs with the TypeScript
SDK's `@diesis/sdk/privacy` provers and pass the bytes in here.

```python
pool = client.privacy.get_shielded_pool_state()
spent = client.privacy.is_shielded_nullifier_spent(nullifier)

client.privacy.withdraw_shielded(
    proof=proof,
    merkle_root=root,
    nullifier_hash=nullifier,
    recipient="0x...",
    amount=10**18,
)
```

## Check node status

**In short.** You can ask the node how far along it is and where your
transaction is.

**Details.** `get_pipeline_status` reports the consensus, execution, and
publication heads and the lag between them. `get_transaction_status` returns
the stage a transaction has reached, such as `preconfirmed` or `executed`.

```python
client.get_pipeline_status()
client.get_transaction_status("0x...")
client.get_rules()
```

## Addresses and ABIs

**In short.** Diesis system contracts live at fixed addresses that start with
`0xD1E515`. The SDK has all of them, plus the interface for each one.

**Details.** `diesis.addresses` holds every system contract and precompile
address as an EIP-55 string. `diesis.abi` exports ABI lists generated from the
contracts, ready for `w3.eth.contract`.

```python
from diesis import addresses
from diesis.abi import DIESISSTAKING_ABI

staking = client.w3.eth.contract(address=addresses.DIESIS_STAKING, abi=DIESISSTAKING_ABI)
```

## Develop

```bash
make test        # pytest
make quality     # ABI drift check, ruff, mypy --strict, tests
make codegen     # regenerate ABIs from ../../diesis/contracts
```

The first `make` target creates `.venv` and installs the dev extras.

## License

MIT
