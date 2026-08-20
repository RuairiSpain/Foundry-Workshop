# Lab 32 — Registering in Agent 365

**Optional — requires Agent 365 licensing.** Ask your instructor if
you're not sure whether you have it; if you don't, read through this
lab and skip the hands-on steps, or watch it as an instructor demo.

You'll register a published Agent Application (Lab 26) with Agent
365's control plane, set an org-wide data-boundary and Content Safety
policy, and see what the control plane can and can't see about an
unregistered agent.

**Surface:** the Agent 365 admin center. It has no public Python SDK
as of writing this workshop — every hands-on step is in the Portal.

## Prerequisites

- Lab 26 complete: at least one published Agent Application.
- Agent 365 licensing.

## Concept: observe, secure, govern — over what's registered

Agent 365 is a control plane, not a runtime — it doesn't run your
agents, it watches, checks, and reports on the ones you've told it
about. That's the catch this lab exists to show: registration is a
separate, additive step from publishing (Lab 26). An agent can be
live, serving real traffic, and still invisible to every org-wide
dashboard and policy check until someone registers it.

## Step 1: Implement the registration and policy logic

Open `starter/agent_365.py`. Implement four functions:

1. `register_agent()` — build an `AgentRegistration` record.
2. `find_unregistered_agents()` — the gap between every agent Foundry
   knows about and every agent Agent 365 has registered.
3. `evaluate_governance_policy()` — check a registration's data
   boundary and Content Safety flag against org policy, reporting
   every violation, not just the first.
4. `build_fleet_dashboard()` — trace volume, failures, and governance
   violations, per registered agent.

Run the tests to check your work:

```bash
python3 -m pytest tests/ -v
```

**Expected output:** 10 passed.

## Step 2: Register the fleet in the admin center

1. Open the Agent 365 admin center and sign in with your tenant admin
   (or delegated) account.
2. For each Agent Application you published in Lab 26, choose
   **Register agent** and fill in the owner, data boundary, and
   whether Content Safety is attached — the same fields
   `register_agent()` takes.
3. Leave one published agent unregistered on purpose.

**Expected output:** the admin center's fleet list shows only the
agents you registered. The one you left out doesn't appear — confirm
that's the same gap `find_unregistered_agents()` reports when you pass
it the full list of agent names from the Foundry Portal.

## Step 3: Set org policy and read the dashboard

1. Under **Policy**, set the required data boundary (match your
   attendee project's region) and require Content Safety.
2. Open **Fleet health**.

**Expected output:** any registration whose data boundary or Content
Safety setting doesn't match — set one up on purpose if none does —
shows a violation, the same one `evaluate_governance_policy()` would
report for the same inputs.

## Where this fits

Lab 33's capstone registers the whole fleet — including the Teams
channel from Lab 31 and the A2A hop to SwiftShip — and treats a clean
`build_fleet_dashboard()` result as one of the checks a governed system
has to pass, not a one-time setup step.
