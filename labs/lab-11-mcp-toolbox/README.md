# Lab 11 — MCP server + Toolbox

You'll build a loyalty-points MCP server with two tools, test it
locally, then register it in the Foundry Toolbox so any agent in the
project can use it without redefining the tools.

**Verified against:** `mcp` 1.29.0 (Model Context Protocol Python SDK),
as of writing this workshop.

## Prerequisites

- Lab 09 complete: you've seen the manual tool-definition pattern this
  lab replaces.

## Concept: MCP vs. a function tool you dispatch yourself

Lab 09's `execute_tool()` was your code deciding which Python function
to call. An MCP server does the same job, but as a standalone process
with a standard protocol — any MCP-aware client, not just this one
agent, can discover and call `get_loyalty_points` without you writing a
dispatcher for each one.

## Step 1: Implement the two tools

Open `starter/mcp_server.py`. Implement both tool functions:

1. `get_loyalty_points()` — call `ledger.get_balance()`. Catch
   `CustomerNotFoundError` and return an error dict instead of raising.
2. `redeem_loyalty_points()` — call `ledger.redeem_points()`. Catch both
   `CustomerNotFoundError` and `InsufficientPointsError` the same way.

Run the tests to check your work:

```bash
python3 -m pytest tests/ -v
```

**Expected output:** 7 passed.

## Step 2: Test it locally with the MCP Inspector

```bash
mcp dev starter/mcp_server.py
```

**Expected output:** a local URL opens the MCP Inspector in your
browser. Under **Tools**, call `get_loyalty_points` with
`customer_email: maya@example.com`.

**Expected output:** `{"customer_email": "maya@example.com", "balance": 1200}`

## Step 3: Register it in the Foundry Toolbox

1. In the Foundry Toolkit, open **Toolbox**.
2. Select **+ Add tool** → **MCP server**.
3. Point it at `starter/mcp_server.py` and name it `cascadia-loyalty`.
4. Confirm both tools appear under the Toolbox entry.

## Step 4: Attach it to Lab 08's prompt agent

1. Open `cascadia-support` in Agent Builder.
2. Under **Tools**, add `cascadia-loyalty` from the Toolbox.
3. In the Agents Playground, ask: `How many loyalty points does
   maya@example.com have?`

**Expected output:** an answer citing 1200 points, without you writing
any new agent code — the same prompt agent from Lab 08 now has a second
capability.

## Where this fits

Lab 25 exposes a different agent over the A2A protocol instead of MCP —
worth comparing once you get there: MCP gives one agent more tools,
A2A lets separate agents delegate whole tasks to each other.
