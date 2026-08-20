# Lab 21 — MAF fundamentals

You'll rebuild Lab 12's Trip Planner three ways, to see Microsoft Agent
Framework's layered design directly: an agent loop, a workflow, and a
harness.

**Verified against:** `agent-framework` 1.14.0, as of writing this
workshop.

## Prerequisites

- Lab 12 complete.

## Concept: three layers, one framework

- **Agent loop** — one agent, one reasoning/act cycle per `.run()`
  call. This is everything you've built with MAF so far.
- **Workflow** — a graph of participants (agents or plain functions)
  that MAF runs together. A workflow with one participant is just an
  agent loop wearing a bigger coat; Lab 22 gives workflows a reason to
  exist by adding more participants.
- **Harness** — an agent loop with extra machinery layered on:
  file access with human-in-the-loop approval, a todo tracker,
  context-window compaction for long sessions. You get this by calling
  a different constructor, not by hand-building more tools the way Lab
  16's sandbox tool was.

## Step 1: Implement all three layers

Open `starter/maf_layers.py`. Implement three functions:

1. `build_agent_loop()` — the same `Agent` construction as Lab 12.
2. `build_workflow()` — build the agent, then wrap it in
   `SequentialBuilder(participants=[agent]).build()`.
3. `build_harness_agent()` — call `create_harness_agent()` with a name,
   `agent_instructions`, the same tool, and `disable_web_search=True`
   (the client in tests doesn't implement web search, so this avoids a
   noisy warning).

Run the tests to check your work:

```bash
python3 -m pytest tests/ -v
```

**Expected output:** 7 passed. One `ExperimentalWarning` about
`FileSystemAgentFileStore` is expected — the harness's file-access layer
is a preview feature.

## Step 2: See the difference in what gets attached

The tests already show it, but confirm it yourself:

```bash
python3 -c "
from starter.maf_layers import build_agent_loop, build_harness_agent
loop = build_agent_loop(object())
harness = build_harness_agent(object())
print('loop middleware:', len(loop.middleware or []))
print('harness middleware:', len(harness.middleware or []))
"
```

**Expected output:** `loop middleware: 0` and `harness middleware: 2` —
the harness attaches machinery a plain agent loop never gets, whether
or not you ever use it.

## Step 3: Run all three against your real deployment

```bash
export FOUNDRY_PROJECT_ENDPOINT="<your project endpoint>"
export LOW_COST_DEPLOYMENT=cascadia-low-cost
python3 starter/maf_layers.py
```

**Expected output:** three replies in a row — `Agent loop:`,
`Workflow:`, `Harness:` — all answering the same gear question, since
one participant in a workflow behaves the same as the plain agent loop
underneath it.

## Where this fits

Lab 22 makes the workflow layer earn its place: multiple participants,
four different orchestration shapes. Lab 23 swaps the harness layer for
the GitHub Copilot SDK's harness instead of MAF's own.
