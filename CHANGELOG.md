# Changelog

## Unreleased

- Breaking (0.2.0): state proofs use Merkle Patricia trie proofs.
  `DiesisClient.get_state_proof` returns the `schemaVersion: 2` response from
  `diesis_getStateProof`: canonical header, MPQ7 certificate and EIP-1186
  account and storage proof. `verify_state_proof` authenticates the account and
  requested slots against a block hash the caller trusts.
  `DiesisClient.get_block_witness` is removed because nodes no longer serve
  `diesis_getBlockWitness`.
- Contract bindings generated with abi-typegen 0.7.0 now provide working web3.py
  view calls and transaction builders. Multi-output view calls return typed
  tuples in Solidity ABI order; they previously advertised dictionary results.
- Contract write methods require an explicit `transaction` dictionary and return
  the built transaction dictionary. Update calls to pass sender/fee/nonce fields
  in that argument; wrappers prepare transactions without signing or submitting.
- Code generation requires explicit qualified artifact inputs and an absolute
  verified `ABI_TYPEGEN` executable. Development provenance tooling requires
  Python 3.11+; SDK runtime compatibility remains Python 3.10+.
