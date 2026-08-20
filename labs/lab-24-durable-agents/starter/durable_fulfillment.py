"""A durable, checkpointed order-fulfillment workflow — check stock,
reserve the item, confirm the order — as a Durable Functions
orchestrator instead of Lab 09's in-process sequence.
"""

from __future__ import annotations

import azure.functions as func
import azure.durable_functions as df

from mock_orders_api.orders import get_order_status, get_warehouse_stock


def check_stock_activity(order_id: str) -> dict:
    """Looks up the order's item and its current total warehouse stock."""
    # TODO(lab-24): call get_order_status(order_id), take its first
    # item's "sku", call get_warehouse_stock(sku), and return a dict
    # with "sku" and "total_stock" (the sum of stock across branches).
    raise NotImplementedError("check_stock_activity is not implemented yet")


def reserve_item_activity(reservation_request: dict) -> dict:
    """Reserves the item — a stand-in, since the fixture data is read-only."""
    return {"sku": reservation_request["sku"], "reserved": True}


def confirm_order_activity(order_id: str) -> dict:
    """Confirms the order and returns the final confirmation."""
    order = get_order_status(order_id)
    return {"order_id": order_id, "status": "confirmed", "items": order.items}


def order_fulfillment_orchestrator(context):
    """The orchestrator: check stock, reserve, confirm — or stop early
    if there's nothing to reserve.
    """
    # TODO(lab-24): get the order_id from context.get_input(). Yield
    # context.call_activity("CheckStock", order_id) and store the
    # result. If total_stock <= 0, return a dict with
    # status="out_of_stock" and the order_id.
    #
    # TODO(lab-24): otherwise, yield context.call_activity("ReserveItem", ...)
    # with a dict containing the sku, then yield
    # context.call_activity("ConfirmOrder", order_id) and return its result.
    raise NotImplementedError("order_fulfillment_orchestrator is not implemented yet")


def register_functions(app: df.DFApp) -> df.DFApp:
    """Registers the orchestrator and its activities on a DFApp instance."""
    app.orchestration_trigger(context_name="context")(order_fulfillment_orchestrator)
    app.activity_trigger(input_name="order_id", activity="CheckStock")(check_stock_activity)
    app.activity_trigger(input_name="reservation_request", activity="ReserveItem")(reserve_item_activity)
    app.activity_trigger(input_name="order_id", activity="ConfirmOrder")(confirm_order_activity)
    return app


app = register_functions(df.DFApp(http_auth_level=func.AuthLevel.FUNCTION))
