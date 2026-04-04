# diesis

Python SDK for the [Diesis](https://diesis.xyz) chain -- exchange, intents, bundles, and patronage.

## Install

```bash
pip install diesis
```

## Quick Start

```python
from diesis import DiesisClient

client = DiesisClient("https://rpc.testnet.diesis.xyz")

# Query exchange
markets = client.exchange.get_markets()
book = client.exchange.get_order_book(markets[0].market_id)

# Check pipeline
status = client.get_pipeline_status()
```
