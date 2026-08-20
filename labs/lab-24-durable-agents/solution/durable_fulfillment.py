"""A durable, checkpointed order-fulfillment workflow — check stock,
reserve the item, confirm the order — as a Durable Functions
orchestrator instead of Lab 09's in-process sequence.

Each `yield` is a checkpoint. If the process restarts mid-run, the
runtime replays the orchestrator from the top, feeding back every
activity result it already has, and only actually re-runs the activity
that hadn't finished — this file's logic doesn't change to get that;
checkpointing is the Durable Functions runtime's job, not ours. That's
also why the orchestrator itself must stay deterministic: no direct
randomness, no direct `datetime.now()`, no I/O other than
`yield context.call_activity(...)`.
"""

from __future__ import annotations

import azure.functions as func
import azure.durable_functions as df

from mock_orders_api.orders import get_order_status, get_warehouse_stock


def check_stock_activity(order_id: str) -> dict:
    """Looks up the order's item and its current total warehouse stock."""
    order = get_order_status(order_id)
    sku = order.items[0]["sku"]
    stock = get_warehouse_stock(sku)
    return {"sku": sku, "total_stock": sum(stock.values())}


def reserve_item_activity(reservation_request: dict) -> dict:
    """Reserves the item.

    The order fixture data is read-only (see mock_orders_api.orders), so
    this returns a confirmation without mutating warehouse stock — a
    real activity would call a real inventory system here instead.
    """
    return {"sku": reservation_request["sku"], "reserved": True}


def confirm_order_activity(order_id: str) -> dict:
    """Confirms the order and returns the final confirmation."""
    order = get_order_status(order_id)
    return {"order_id": order_id, "status": "confirmed", "items": order.items}


def order_fulfillment_orchestrator(context):
    """The orchestrator: check stock, reserve, confirm — or stop early
    if there's nothing to reserve.

    Deliberately a plain generator function, not decorated with
    `@app.orchestration_trigger` here — that decorator wraps it in a
    FunctionBuilder the Functions host uses, which is not directly
    callable the way this lab's tests need. `register_functions()`
    below applies the real decorators for deployment.
    """
    order_id = context.get_input()
    stock_info = yield context.call_activity("CheckStock", order_id)
    if stock_info["total_stock"] <= 0:
        return {"status": "out_of_stock", "order_id": order_id}

    yield context.call_activity("ReserveItem", {"sku": stock_info["sku"]})
    confirmation = yield context.call_activity("ConfirmOrder", order_id)
    return confirmation


def register_functions(app: df.DFApp) -> df.DFApp:  # pragma: no cover - decorator wiring, exercised by the real host
    """Registers the orchestrator and its activities on a DFApp instance."""
    # `activity=` is explicit on purpose: it must match the string name
    # `order_fulfillment_orchestrator` passes to `call_activity()` above,
    # and that's easy to get wrong silently if left to a naming default.
    app.orchestration_trigger(context_name="context")(order_fulfillment_orchestrator)
    app.activity_trigger(input_name="order_id", activity="CheckStock")(check_stock_activity)
    app.activity_trigger(input_name="reservation_request", activity="ReserveItem")(reserve_item_activity)
    app.activity_trigger(input_name="order_id", activity="ConfirmOrder")(confirm_order_activity)
    return app


app = register_functions(df.DFApp(http_auth_level=func.AuthLevel.FUNCTION))  # pragma: no cover
