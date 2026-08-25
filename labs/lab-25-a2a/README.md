# Lab 25 — Agent-to-agent (A2A)

You'll stand up SwiftShip — an external partner agent — and have
Cascadia's Trip Planner delegate shipping-ETA questions to it over the
A2A protocol, instead of implementing shipping logic itself.

**Verified against:** `agent_framework.a2a` in `agent-framework` 1.14.0,
as of writing this workshop.

## Prerequisites

- Lab 12 complete.

## A note on SwiftShip

SwiftShip is a stand-in you run yourself, in
`starter/swiftship_server.py` — not a real courier's live system.
That's normal for a workshop, and it still teaches the real pattern:
one agent process delegating a task to a completely separate agent
process it doesn't share code with, over a standard protocol.

## Step 1: Implement SwiftShip's ETA logic

Open `starter/swiftship_server.py`. Implement `estimate_shipping_eta()`:
raise `ValueError` for an unknown zone, return that zone's ETA for a
same-zone shipment, and the `"national"` ETA otherwise.

## Step 2: Implement the Trip Planner's delegation

Open `starter/trip_planner_client.py`. Implement two functions:

1. `build_swiftship_client()` — an `A2AAgent` pointed at SwiftShip's
   URL.
2. `build_trip_planner_with_swiftship()` — build the SwiftShip client,
   then return a Trip Planner `Agent` with
   `tools=[swiftship.as_tool()]`. `.as_tool()` is what turns a whole
   remote agent into something another agent can call as a single tool.

Run the tests to check your work:

```bash
LAB_TARGET=starter python3 -m pytest tests/ -v
```

**Expected output:** 7 passed. Nothing here makes a network call —
`A2AAgent`'s constructor is lazy, the same pattern as
`FoundryChatClient` and `GitHubCopilotAgent`.

## Step 3: Run both sides for real

In one terminal, start SwiftShip:

```bash
python3 starter/swiftship_server.py
```

**Expected output:** `SwiftShip A2A executor ready: ...` — see the
comment in `main()` for what a real deployment adds on top (an ASGI
server exposing the A2A endpoint).

In a second terminal, run the Trip Planner:

```bash
export FOUNDRY_PROJECT_ENDPOINT="<your project endpoint>"
export SWIFTSHIP_A2A_URL="http://localhost:8001/a2a"
python3 starter/trip_planner_client.py
```

**Expected output:** a shipping ETA, sourced from SwiftShip's process,
not the Trip Planner's own reasoning.

## Step 4: Read the delegation chain in the trace

Open **Tracing** for the Trip Planner's run.

**Expected output:** a trace step showing the call out to `swiftship`,
distinct from a normal tool call — this is what makes A2A delegation
auditable across a process boundary, the same as any other tool call in
this workshop, just crossing a network hop instead of an in-process
function call.

## Where this fits

Lab 32 registers this same delegation chain — Trip Planner to SwiftShip
— in Agent 365's org-wide view, so a platform team can see across the
process boundary too, not just within one agent's own trace.
