# Lab 24 — Durable Agents and Durable Functions

You'll rebuild an order-fulfillment sequence as a Durable Functions
orchestrator: check stock, reserve the item, confirm the order — one
that survives a restart partway through, instead of starting over.

**Verified against:** `azure-functions-durable` 1.7.0, as of writing
this workshop.

## Prerequisites

- Lab 09 complete.

## Concept: a checkpoint per `yield`

A Durable Functions orchestrator is a plain Python generator. Every
`yield context.call_activity(...)` is a checkpoint the runtime records.
If the process crashes after "reserve the item" completes but before
"confirm the order" starts, the runtime doesn't restart from step one —
it replays the orchestrator function from the top, feeding back every
activity result it already has, and only actually re-executes the one
activity that hadn't finished yet. The orchestrator function has to stay
deterministic for that to work: no direct randomness, no
`datetime.now()`, no I/O other than `yield context.call_activity(...)`.

## Step 1: Implement the activity and the orchestrator

Open `starter/durable_fulfillment.py`. Implement two functions:

1. `check_stock_activity()` — look up the order, take its first item's
   SKU, and return the SKU with its total stock across branches.
2. `order_fulfillment_orchestrator()` — get the order ID from
   `context.get_input()`. Yield a `CheckStock` call. If there's no
   stock, return early with an `out_of_stock` status. Otherwise yield
   `ReserveItem` and `ConfirmOrder` in turn, returning the final
   confirmation.

Run the tests to check your work:

```bash
LAB_TARGET=starter python3 -m pytest tests/ -v
```

**Expected output:** 6 passed. These tests never start a Functions
host — `FakeDurableContext` stands in for the real
`DurableOrchestrationContext`, and the tests drive the orchestrator
generator directly with `next()` and `.send()`, the standard way to
unit-test one.

## Step 2: Run it locally

```bash
cd starter
func start
```

In a second terminal, start an instance:

```bash
curl -X POST http://localhost:7071/api/orchestrators/order_fulfillment_orchestrator \
  -H "Content-Type: application/json" -d '"CO-10231"'
```

**Expected output:** a status URL. Poll it:

```bash
curl <the statusQueryGetUri from the previous response>
```

**Expected output:** `"runtimeStatus": "Completed"` with the final
confirmation in `output`.

## Step 3: Prove the restart survives

1. Start another instance the same way.
2. While it's mid-run (check its status quickly after starting), stop
   `func start` with `Ctrl+C` and restart it.
3. Poll the same status URL again.

**Expected output:** `"runtimeStatus": "Completed"` — the orchestration
finished despite the restart, without you writing any retry logic.

## Where this fits

Lab 33's capstone treats this durable workflow as one more specialist
behind the Magentic manager from Lab 22 — an orchestration pattern that
survives restarts, sitting alongside ones that don't need to.
