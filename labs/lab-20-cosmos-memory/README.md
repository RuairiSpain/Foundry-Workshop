# Lab 20 — Cosmos DB-backed memory

You'll store conversation turns in your own Cosmos DB container — the
Agent Memory Toolkit pattern — and distill them into a small customer
profile, instead of relying on Lab 19's managed memory store.

**Verified against:** `azure-cosmos` 4.16.3, as of writing this workshop.

## Prerequisites

- Lab 19 complete.
- Your Cosmos DB container exists: `infra/cosmos/provision_attendee_container.sh`
  created `mem-<your-attendee-id>` in the shared `workshop-memory`
  database, scoped to only your credentials.

## Concept: why bring your own memory store

Lab 19's native memory is fully managed — you don't choose where facts
live or how long they're kept. A Cosmos-backed store is more work, in
exchange for direct control: data residency, retention policy, and the
ability to query raw conversation history yourself, not just distilled
facts.

## Step 1: Implement the storage and distillation functions

Open `starter/cosmos_memory.py`. Implement four functions:

1. `build_memory_document()` — a dict with `id`, `threadId` (the
   partition key), `customerEmail`, `role`, and `content`.
2. `store_turn()` — build a document and call
   `container.upsert_item()`.
3. `search_memory_by_customer()` — call `container.query_items()` with
   a SQL `query` filtering on `c.customerEmail`, its bound
   `parameters`, and `enable_cross_partition_query=True` (customerEmail
   isn't the partition key, so the match can be in any partition).
4. `distill_profile()` — raise `ValueError` for an empty turn list.
   Otherwise collect every SKU mentioned across all turns into a sorted,
   deduplicated list, and return a `CustomerProfile`.

Run the tests to check your work:

```bash
LAB_TARGET=starter python3 -m pytest tests/ -v
```

**Expected output:** 8 passed.

## Step 2: Run it against your real container

```bash
export COSMOS_ACCOUNT_ENDPOINT="<your Cosmos account endpoint>"
export COSMOS_ACCOUNT_KEY="<your Cosmos key or use Entra ID auth — see infra/README.md>"
export COSMOS_CONTAINER_NAME="mem-<your-attendee-id>"
python3 starter/cosmos_memory.py
```

**Expected output:** a `CustomerProfile` with `mentioned_skus=['TENT-2P-GRN']`
and `turn_count=1`.

## Step 3: Confirm your container is actually isolated

Ask another attendee for their container name and try reading it:

```bash
export COSMOS_CONTAINER_NAME="mem-<someone-else's-attendee-id>"
python3 starter/cosmos_memory.py
```

**Expected output:** an authorization error. Your RBAC grant is scoped
to your own container only — this is Lab 09's tool-level trust
boundary, applied at the data layer instead.

## Where this fits

This closes Module 5. Module 6 starts at Lab 21, returning to
Microsoft Agent Framework — this time to compose multiple agents, not
just add capabilities to one.
