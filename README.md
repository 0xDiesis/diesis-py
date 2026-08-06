# diesis

Python SDK for the [Diesis](https://diesis.xyz) chain -- exchange, intents, bundles, and patronage.

## Install

The `diesis-sdk` distribution is not published on PyPI. Install it from an
authenticated source checkout; the Python import package remains `diesis`:

```bash
python -m pip install .
```

## Quick Start

```python
from diesis import DiesisClient
from diesis.intents.types import OrderFlags, OrderIntent

client = DiesisClient("https://rpc.testnet.diesis.xyz")

# Query exchange
markets = client.exchange.get_markets()
book = client.exchange.get_order_book(markets[0].market_id)

# Sign a canonical EIP-712 v2 exchange intent
intent = OrderIntent(
    trader="0x0000000000000000000000000000000000000001",
    market_id="0x" + "01" * 32,
    side=0,
    order_type=0,
    price=100,
    amount=50,
    nonce=1,
    flags=int(OrderFlags.REDUCE_ONLY),
)
signed = client.sign_order_intent(intent)

# Check pipeline
status = client.get_pipeline_status()
```

Order intent signing follows the same v2 EIP-712 field order and domain as the
TypeScript SDK and Rust exchange wire crate. The Python SDK validates addresses,
bytes32 fields, unsigned integer bounds, and known order flags before signing so
bad payloads fail before a wallet signature is produced.
