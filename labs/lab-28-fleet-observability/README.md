# Lab 28 — Finding expensive, slow, and failing agents

You'll triage a fleet-wide batch of traces to find a planted cost spike,
a planted latency regression, and a planted failure — the same
metric-to-trace jump the Portal's tracing view gives you, done here in
code so the analysis logic is testable.

**Verified against:** Azure Monitor / Application Insights trace schema
concepts, as of writing this workshop.

## Prerequisites

- Lab 15 complete.

## Step 1: Implement the analysis functions

Open `starter/fleet_observability.py`. Implement five functions:

1. `find_slow_traces()` — filter to `duration_ms > threshold_ms`, sorted
   slowest first.
2. `find_expensive_traces()` — filter to `cost_usd > threshold_usd`,
   sorted most expensive first.
3. `find_failed_traces()` — filter to `status != "success"`.
4. `summarize_by_agent()` — group by `agent_name`, and build an
   `AgentStats` per agent with trace count, total cost, average
   duration, and failure rate.
5. `correlate_metric_to_trace()` — find the trace matching a given
   `trace_id`, raising `KeyError` if it doesn't exist.

Run the tests to check your work:

```bash
python3 -m pytest tests/ -v
```

**Expected output:** 8 passed — each finding exactly the one planted
outlier it's supposed to.

## Step 2: Run it against the fixture data

```bash
python3 starter/fleet_observability.py
```

**Expected output:**

```
Slow: ['tr-007']
Expensive: ['tr-005']
Failed: ['tr-004']
```

## Step 3: Find the same three things in the real Portal

1. Open the Foundry Portal's **Tracing** view, scoped to the whole
   project instead of one agent.
2. Sort by duration — find your own slow trace from Lab 22's Magentic
   run.
3. Open the **Cost** view and find whichever agent used the most tokens
   this session.

The equivalent of this lab's functions as a KQL query against Log
Analytics:

```kql
AppTraces
| where TimeGenerated > ago(1h)
| extend AgentName = tostring(Properties["agent_name"]),
         DurationMs = todouble(Properties["duration_ms"]),
         CostUsd = todouble(Properties["cost_usd"])
| where DurationMs > 2000 or CostUsd > 0.1 or Properties["status"] != "success"
| project TimeGenerated, AgentName, DurationMs, CostUsd, Properties["status"]
```

**Expected output:** the same three trace types this lab's Python found
— slow, expensive, failed — read from real telemetry instead of the
fixture data.

## Where this fits

Lab 30's AI Gateway adds per-attendee rate limits precisely so one
agent's cost spike — like `tr-005` in this lab's fixture — can't starve
everyone else's token budget the way it could without a gateway.
