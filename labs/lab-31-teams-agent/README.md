# Lab 31 — A Teams agent

**Optional — requires M365 tenant admin.** Ask your instructor if
you're not sure whether you have it; if you don't, read through this
lab and skip the hands-on steps, or watch it as an instructor demo.

You'll package Lab 09's order-status agent for Microsoft Teams: verify
the caller's tenant claim before it answers anything, format its reply
as a Teams message, and side-load it into a real Teams client with the
M365 Agents Toolkit.

**Verified against:** `microsoft-agents-hosting-core` 1.4.0's
`ClaimsIdentity` and `MessageFactory`, as of writing this workshop.

## Prerequisites

- Lab 09 complete.
- M365 tenant admin access, and the M365 Agents Toolkit extension for
  VS Code.

## Concept: one more channel, not a new agent

A Teams deployment doesn't change what the order-status agent knows or
which tools it calls — Lab 09 already built that. It adds two things
any channel needs: proof of who's calling (channel authentication) and
a reply shaped the way the channel expects it (a Teams `Activity`
instead of a plain string). Keep those concerns in their own functions,
the way this lab does, and the same agent works behind Teams, a REST
API, or the CLI script Lab 09 already runs.

## Step 1: Implement the channel layer

Open `starter/teams_agent.py`. Implement four functions:

1. `build_teams_manifest()` — the Teams app manifest dict.
2. `authenticate_teams_request()` — build a `ClaimsIdentity`, reject a
   claims-free (anonymous) caller, reject the wrong tenant.
3. `format_reply_for_teams()` — wrap a reply string in a Teams
   `Activity` with `MessageFactory.text()`.
4. `handle_teams_message()` — authenticate, then ask, then format.

Run the tests to check your work:

```bash
LAB_TARGET=starter python3 -m pytest tests/ -v
```

**Expected output:** 8 passed.

## Step 2: Confirm authentication actually blocks the wrong tenant

Read `test_handle_teams_message_never_asks_the_agent_when_auth_fails`.
Notice the fake `ask()` function records every call it receives — the
test proves the agent is never asked anything when authentication
fails, not just that an error was raised. A channel layer that calls
the agent first and checks the caller's identity after has already
leaked whatever the agent said.

## Step 3: Package and side-load into Teams

```bash
atk new  # if you haven't scaffolded an M365 Agents Toolkit project yet
atk provision
atk package
```

Point the generated project's bot logic at `handle_teams_message()`
from `solution/teams_agent.py`, and its `manifest.json` at
`build_teams_manifest()`'s output. Then:

```bash
atk deploy
atk publish  # side-loads the app package into your Teams tenant
```

**Expected output:** the Cascadia Order Status app appears in Teams'
**Apps** panel. Open it and ask about an order.

## Step 4: Ask it about a real order, in Teams

Send: `What's the status of order CO-10231?`

**Expected output:** the same answer Lab 09's CLI script gave you, this
time as a Teams message. Check the request's `tid` claim in the M365
Agents Toolkit's debug console — it's your real tenant ID, verified by
`authenticate_teams_request()` before the agent saw the question.

## Where this fits

Lab 33's capstone treats every channel — this one, the CLI, the A2A
hop to SwiftShip — as one more entry point into the same governed
fleet, none of them trusted until `authenticate_teams_request()` (or
its equivalent for that channel) says so.
