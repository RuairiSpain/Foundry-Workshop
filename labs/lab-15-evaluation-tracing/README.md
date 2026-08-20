# Lab 15 — Evaluation, tracing, and debugging

You'll build a small eval dataset covering groundedness, relevance, and
safety, run a batch evaluation, then diagnose a deliberately broken
tool call the way you'd read it from a trace.

**Verified against:** Foundry Portal tracing and evaluation views, as of
writing this workshop.

## Prerequisites

- Lab 09 complete: you'll reuse its tool-calling pattern to trigger a
  failure on purpose.

## Step 1: Implement the evaluation metrics

Open `starter/evaluation.py`. Implement six functions:

1. `score_groundedness()` — same logic as Lab 14's `score_reply()`.
2. `score_relevance()` — `False` if the reply contains a canned refusal
   phrase from `REFUSAL_PHRASES`, `True` otherwise.
3. `score_safety()` — `False` if the reply contains a forbidden phrase,
   `True` otherwise.
4. `evaluate_one()` — call the model, then score groundedness,
   relevance, and safety on the reply.
5. `run_batch_evaluation()` — call `evaluate_one()` once per dataset
   item.
6. `find_failures()` — filter to results where `.passed` is `False`.

Then implement `diagnose_tool_call_failure()`: loop over
`run.tool_calls_made`, and return a message naming the tool and its
error the first time a call's result is an error dict.

Run the tests to check your work:

```bash
python3 -m pytest tests/ -v
```

**Expected output:** 10 passed.

## Step 2: Run the batch evaluation for real

```bash
export LOW_COST_DEPLOYMENT=cascadia-low-cost
python3 starter/evaluation.py
```

**Expected output:** a `N/3 passed` line. If the safety question fails,
your agent is leaking order IDs it shouldn't — worth fixing before Lab
29's Responsible AI guardrails, not after.

## Step 3: Break a tool call on purpose, then diagnose it

1. In the Foundry Portal, open Lab 09's `cascadia-order-status` agent.
2. Ask it about an order ID that doesn't exist, like `CO-00000`.
3. Open **Tracing** for that run and find the `get_order_status` tool
   call.

**Expected output:** the trace shows the tool call's input
(`{"order_id": "CO-00000"}`) and its output (an error dict) side by
side — exactly what `diagnose_tool_call_failure()` reads from the run
record in code instead.

## Where this fits

Lab 27 wires `run_batch_evaluation()` into a CI/CD step that blocks a
new agent version from publishing if it regresses. Lab 28 does the same
kind of trace reading you just did in step 3, but across the whole
agent fleet instead of one run you triggered on purpose.
