# Lab 22 — Workflow orchestration patterns

You'll build the same triage-to-specialist scenario four ways — three
fixed shapes, then Magentic, an open-ended planner-orchestrator loop —
and see why the workshop's multi-agent scenario runs on the last one.

**Verified against:** `agent_framework.orchestrations` in
`agent-framework` 1.14.0, as of writing this workshop.

## Prerequisites

- Lab 21 complete.

## Step 1: Implement the three fixed shapes

Open `starter/orchestration_patterns.py`. Implement three functions:

1. `build_sequential_workflow()` — `SequentialBuilder(participants=[triage, order]).build()`.
   Each participant sees the previous one's output, in order.
2. `build_concurrent_workflow()` — `ConcurrentBuilder(participants=[order, trip_planner]).build()`.
   Both run on the same input at once and fan in to one result.
3. `build_handoff_workflow()` — build both agents with
   `require_per_service_call_history_persistence=True` (Handoff
   requires it — you'll see why in step 2), then
   `HandoffBuilder(participants=[triage, order]).with_start_agent(triage).add_handoff(triage, [order]).build()`.

## Step 2: See Handoff enforce its own requirement

Before implementing the flag, try building a handoff workflow without
`require_per_service_call_history_persistence=True` on either agent.

**Expected output:** `ValueError: Handoff workflows require all
participant agents to have 'require_per_service_call_history_persistence=True'.`
Handoffs can short-circuit a tool call mid-flight, so local history has
to stay consistent with the service when that happens — Handoff won't
let you build a workflow that could get this wrong silently.

## Step 3: Implement Magentic

Implement `build_magentic_workflow()`: build a manager agent and the
four specialists (triage, order, trip-planner, innovation — all already
defined in the file), and return
`MagenticBuilder(participants=[...], manager_agent=manager).build()`.

Unlike the first three builders, Magentic requires an explicit manager —
building one with no `manager`, `manager_factory`, `manager_agent`, or
`manager_agent_factory` raises immediately. Sequential and Concurrent
just run whichever participants you give them; Magentic needs something
to plan and delegate.

Run the tests to check your work:

```bash
python3 -m pytest tests/ -v
```

**Expected output:** 5 passed. None of these call `.run()` — every
builder's `.build()` is synchronous, so a workflow's participants are
inspectable through `get_executors_list()` without a live model.

## Step 4: Run the Magentic workflow for real

```bash
export FOUNDRY_PROJECT_ENDPOINT="<your project endpoint>"
export ROUTER_DEPLOYMENT=cascadia-router
python3 starter/orchestration_patterns.py
```

**Expected output:** the manager plans, delegates to whichever
specialists the question needs, and the innovation participant proposes
one trail-bundle idea in the final answer — read the result to see which
specialists it actually called, since Magentic decides that at runtime,
not from a fixed graph.

## Where this fits

Lab 23 swaps this workflow's harness layer for the GitHub Copilot SDK's.
Lab 24 rebuilds a fixed-shape workflow like Lab 22's sequential one as a
Durable Function, so it survives a restart mid-run. Lab 33's capstone
runs this same Magentic workflow behind the AI Gateway, with evaluation
gates and full tracing on top.
