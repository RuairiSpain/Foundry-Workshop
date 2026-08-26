# Beta debrief — Lab 20 (Cosmos DB-backed memory)

## What the simulated attendee did

Implemented all four functions using only the README's Step 1 list and the
starter file's TODO comments/docstrings:

- `build_memory_document()` — built the dict exactly as specified (`id`,
  `threadId`, `customerEmail`, `role`, `content`).
- `store_turn()` — built a document and called `container.upsert_item()`.
- `search_memory_by_customer()` — called `container.query_items()` with the
  SQL query, bound parameter, and `enable_cross_partition_query=True`
  exactly as specified.
- `distill_profile()` — raised `ValueError` for an empty list, collected
  `SKU_PATTERN` matches into a sorted set, and returned a `CustomerProfile`.
  Message used: `"distill_profile requires at least one turn"`.

## Where it diverged

`LAB_TARGET=starter python3 -m pytest tests/ -v` failed one test:

```
test_distill_profile_raises_for_an_empty_turn_list FAILED
    with pytest.raises(ValueError, match="zero turns"):
E   AssertionError: Regex pattern did not match.
E     Expected regex: 'zero turns'
E     Actual message: 'distill_profile requires at least one turn'
```

The starter's TODO comment says only "raise ValueError for an empty list" —
it gives no hint that the test asserts on the *wording* of the message
(`match="zero turns"`). Every other function's TODO in this file spells out
the exact call signature/arguments needed to satisfy the tests; this is the
one spot where the test depends on message text the TODO doesn't mention.
Everything else matched the solution's behavior on the first pass.

## Judgment

This is a minor but real README/starter gap — worth a one-line fix rather
than leaving a first-time attendee to guess wording from a regex in a
pytest failure. Behavior (control flow, dataclass fields, SKU collection)
was otherwise identical to `solution/cosmos_memory.py`.

## Fix applied

Reworded the `distill_profile` TODO comment in `starter/cosmos_memory.py`
to say the message must mention "zero turns", matching what the test
actually checks. No implementation logic was added back to the starter —
it still raises `NotImplementedError` with the TODO stub.
