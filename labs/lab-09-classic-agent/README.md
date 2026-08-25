# Lab 09 — Classic agent

You'll build an order-status agent in code, with real Python functions
as tools, and exercise it across two turns in the same thread.

**Verified against:** `azure-ai-agents` 1.1.0's `AgentsClient`, as of
writing this workshop.

## Prerequisites

- Lab 03 complete.

## Concept: classic agent vs. prompt agent

Lab 08's prompt agent was fully managed — no code, no tools you wrote
yourself. A classic agent is the opposite: you define its tools as real
Python functions, and your code decides how to run them when the
service asks. That's more work, and it's what makes function tools
possible at all — a prompt agent can't call `mock_orders_api.orders`.

## Step 1: Implement the agent and its tools

Open `starter/order_status_agent.py`. Implement three functions:

1. `create_order_status_agent()` — call `agents_client.create_agent()`
   with both tool definitions already provided in the file
   (`ORDER_STATUS_TOOL`, `LIST_ORDERS_TOOL`).
2. `execute_tool()` — dispatch `"get_order_status"` and
   `"list_orders_for_customer"` to their real implementations in
   `mock_orders_api.orders`. Catch `OrderNotFoundError` and return an
   error dict instead of raising. Raise `ValueError` for any other tool
   name.
3. `ask_in_thread()` — add a user message to an existing thread, process
   a run with `tool_executor=execute_tool`, and return the last
   message's content.

Run the tests to check your work:

```bash
LAB_TARGET=starter python3 -m pytest tests/ -v
```

**Expected output:** 8 passed.

## Step 2: Run it against your real project

```bash
export LOW_COST_DEPLOYMENT=cascadia-low-cost
python3 starter/order_status_agent.py
```

**Expected output:**

```
Turn 1: Your order CO-10231 has shipped via SwiftShip...
Turn 2: Order CO-10245 is still processing...
```

Both turns run in the same thread — that's what let the agent answer
"what about CO-10245?" without you repeating who's asking.

## Step 3: Watch a tool call in the trace

1. Open the Foundry Portal's **Tracing** view.
2. Find the run from turn 1.
3. Open its detail and find the `get_order_status` tool call — you'll
   see the exact arguments the model chose and the value your function
   returned.

**Expected output:** a trace step named `get_order_status` with
`{"order_id": "CO-10231"}` as its input.

## Where this fits

Lab 10 moves `get_warehouse_stock` and `get_shipping_eta` — two more
`mock_orders_api` functions — out of this in-process pattern and behind
an Azure Functions HTTP endpoint instead. Lab 11 packages a different
capability (loyalty points) as an MCP server in the Toolbox, so you can
compare "tool as a Python function you dispatch yourself" against "tool
as an MCP server the platform hosts for you."
