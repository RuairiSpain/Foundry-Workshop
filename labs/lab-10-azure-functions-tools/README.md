# Lab 10 — Tools on Azure Functions

You'll move two tools — warehouse stock and shipping ETA — out of the
in-process pattern from Lab 09 and behind a deployed Azure Functions
HTTP endpoint, then call them from an agent over the network instead of
a direct function call.

**Verified against:** `azure-functions` 1.25.0, Azure Functions Core
Tools 4.x, as of writing this workshop.

## Prerequisites

- Lab 09 complete.
- Azure Functions Core Tools installed (`func --version` should print
  4.x).

## Step 1: Implement the Function app

Open `starter/function_app.py`. Implement two route handlers:

1. `warehouse_stock()` — read `sku` from `req.params`. Return 400 if
   missing. Otherwise call `get_warehouse_stock()` and return the
   result. Catch `SkuNotFoundError` and return 404.
2. `shipping_eta()` — the same pattern for `order_id` and
   `get_shipping_eta()`.

Run the tests to check your work:

```bash
LAB_TARGET=starter python3 -m pytest tests/test_function_app.py -v
```

**Expected output:** 7 passed. These tests call your handlers directly,
with no Functions host running — that's what `azure.functions.HttpRequest`
is for.

## Step 2: Run it locally

```bash
cd starter
func start
```

**Expected output:** a local endpoint at
`http://localhost:7071/api/warehouse-stock`. In a second terminal:

```bash
curl "http://localhost:7071/api/warehouse-stock?sku=TENT-2P-GRN"
```

**Expected output:** `{"branch-seattle": 4, "branch-portland": 0, "warehouse-central": 22}`

## Step 3: Deploy it and implement the client

1. Deploy: `func azure functionapp publish <your-function-app-name>`.
2. Copy the function URL and, from the Portal, a function key.
3. Export both:

   ```bash
   export WAREHOUSE_FUNCTION_URL="https://<your-function-app-name>.azurewebsites.net"
   export WAREHOUSE_FUNCTION_KEY="<your function key>"
   ```

4. Open `starter/function_tool_client.py`. Implement three functions:
   - `call_warehouse_stock()` — build params, call `http_get()`, raise
     `FunctionToolError` on a non-200 response, otherwise return the
     parsed JSON.
   - `call_shipping_eta()` — the same pattern for `/api/shipping-eta`.
   - `execute_remote_tool()` — dispatch to whichever of the two the tool
     name matches, mirroring Lab 09's `execute_tool()`.

Run the tests to check your work:

```bash
LAB_TARGET=starter python3 -m pytest tests/test_function_tool_client.py -v
```

**Expected output:** 10 passed.

## Step 4: Call the deployed function for real

```bash
python3 starter/function_tool_client.py
```

**Expected output:** `Warehouse stock: {'branch-seattle': 4, ...}`

## Where this fits

`execute_remote_tool()` has the exact same signature as Lab 09's
`execute_tool()` — you can pass either one to
`agents_client.runs.create_and_process(tool_executor=...)` without
changing anything else about the agent. Lab 11 packages a third
capability, loyalty points, as an MCP server instead of a Functions
endpoint, and compares that pattern against this one.
