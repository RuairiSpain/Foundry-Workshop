"""Azure Function app exposing warehouse-stock and shipping-ETA lookups
over HTTP, so Cascadia's agents can call them as a deployed tool instead
of an in-process Python function.
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
    # TODO(lab-10): read "sku" from req.params. If missing, return a 400
    # via _json_response({"error": "sku is required"}, status_code=400).
    #
    # TODO(lab-10): read the optional "branch_id" param, call
    # get_warehouse_stock(sku, branch_id), and return the result with
    # _json_response(). Catch SkuNotFoundError and return a 404.
    raise NotImplementedError("warehouse_stock is not implemented yet")


@app.route(route="shipping-eta")
def shipping_eta(req: func.HttpRequest) -> func.HttpResponse:
    """GET /api/shipping-eta?order_id=<order_id>"""
    # TODO(lab-10): read "order_id" from req.params. If missing, return
    # a 400. Otherwise call get_shipping_eta(order_id) and return
    # {"eta": ...}. Catch OrderNotFoundError and return a 404.
    raise NotImplementedError("shipping_eta is not implemented yet")
