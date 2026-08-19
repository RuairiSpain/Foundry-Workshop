"""Azure Function app exposing warehouse-stock and shipping-ETA lookups
over HTTP, so Cascadia's agents can call them as a deployed tool instead
of an in-process Python function.

Deploy with `func azure functionapp publish <name>` (see README.md). The
handlers wrap the same mock_orders_api.orders functions Lab 09 called
directly — only the transport changes.
"""

from __future__ import annotations

import json

import azure.functions as func

from mock_orders_api.orders import OrderNotFoundError, SkuNotFoundError, get_shipping_eta, get_warehouse_stock

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)


def _json_response(payload: dict, *, status_code: int = 200) -> func.HttpResponse:
    return func.HttpResponse(json.dumps(payload), status_code=status_code, mimetype="application/json")


@app.route(route="warehouse-stock")
def warehouse_stock(req: func.HttpRequest) -> func.HttpResponse:
    """GET /api/warehouse-stock?sku=<sku>&branch_id=<optional>"""
    sku = req.params.get("sku")
    if not sku:
        return _json_response({"error": "sku is required"}, status_code=400)
    branch_id = req.params.get("branch_id")
    try:
        stock = get_warehouse_stock(sku, branch_id)
    except SkuNotFoundError:
        return _json_response({"error": f"Unknown SKU: {sku}"}, status_code=404)
    return _json_response(stock)


@app.route(route="shipping-eta")
def shipping_eta(req: func.HttpRequest) -> func.HttpResponse:
    """GET /api/shipping-eta?order_id=<order_id>"""
    order_id = req.params.get("order_id")
    if not order_id:
        return _json_response({"error": "order_id is required"}, status_code=400)
    try:
        eta = get_shipping_eta(order_id)
    except OrderNotFoundError:
        return _json_response({"error": f"Unknown order: {order_id}"}, status_code=404)
    return _json_response({"eta": eta})
