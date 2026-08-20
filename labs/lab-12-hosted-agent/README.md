# Lab 12 — Hosted agent

You'll build Cascadia's Trip Planner as a Microsoft Agent Framework
(MAF) agent — a different SDK from every agent so far — containerize
it, and deploy it as a hosted agent.

**Verified against:** `agent-framework` 1.14.0, as of writing this
workshop.

## Prerequisites

- Lab 03 complete.

## Concept: why a different SDK for this agent

Labs 08 and 09 used `azure-ai-projects`' agents surface directly — fine
for agents that live entirely inside Foundry. MAF is a framework-level
SDK: the same `Agent` class works against Foundry, OpenAI, Anthropic, or
any other supported backend, which is what makes Module 6's multi-agent
workflows and alternate harnesses possible later. This lab is the
simplest possible MAF agent — one agent, one tool — so those later labs
have something familiar to build on.

## Step 1: Implement the agent and its tool

Open `starter/trip_planner_agent.py`. Implement two functions:

1. `suggest_gear_for_trail()` — look up `trail_name` in
   `load_trail_database()`. If it's missing, list the known trail names
   instead of guessing. Otherwise return a plain-language string with
   the difficulty, distance, and recommended gear.
2. `build_trip_planner_agent()` — return an `Agent` built from `client`,
   with a name, instructions, and `tools=[suggest_gear_for_trail]`. Name
   the `suggest_gear_for_trail` tool by its exact function name
   somewhere in the instructions text — that's what tells the model
   which tool to call, and it's how the tests confirm the tool is wired
   in without making a live model call.

Run the tests to check your work:

```bash
LAB_TARGET=starter python3 -m pytest tests/ -v
```

**Expected output:** 6 passed. These tests never make a model call —
`Agent`'s constructor is synchronous, so its instructions and tools are
checkable directly through `agent.default_options`.

## Step 2: Run it against your real deployment

```bash
export FOUNDRY_PROJECT_ENDPOINT="<your project endpoint>"
export LOW_COST_DEPLOYMENT=cascadia-low-cost
python3 starter/trip_planner_agent.py
```

**Expected output:** a short paragraph recommending gear for the
Cascade Pass Loop, citing the tent, boots, and trekking poles from the
trail database.

## Step 3: Containerize it

1. Open the Foundry Toolkit's **Hosted Agents** view.
2. Select **+ New hosted agent** and point it at
   `starter/trip_planner_agent.py`.
3. Let the Toolkit generate the Dockerfile and build the container.

**Expected output:** a built image, ready to deploy.

## Step 4: Deploy and trace it

1. Deploy the hosted agent from the Toolkit.
2. Open the Agents Playground and ask the same trip-planning question.
3. Open **Tracing** for the run.

**Expected output:** a trace showing the model's decision to call
`suggest_gear_for_trail`, the tool's return value, and the final reply —
end to end, from inside VS Code.

## Where this fits

Lab 21 rebuilds this exact agent locally to introduce MAF's harness and
workflow layers. Lab 25 exposes a version of it over A2A so another
agent can delegate trip-planning tasks to it directly.
