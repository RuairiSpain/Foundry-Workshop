"""Tests for solution/function_app.py.

azure.functions lets you construct a request and call a route handler
directly, with no running Functions host — that's what makes this
testable at all without deploying anything.
"""

import json

import azure.functions as func

from solution.function_app import shipping_eta, warehouse_stock


def _get(handler, params):
    request = func.HttpRequest(method="GET", url="/api/test", params=params, body=b"")
    return handler(request)


def test_warehouse_stock_returns_stock_for_a_known_sku():
    response = _get(warehouse_stock, {"sku": "TENT-2P-GRN"})

    assert response.status_code == 200
    assert json.loads(response.get_body()) == {"branch-seattle": 4, "branch-portland": 0, "warehouse-central": 22}


def test_warehouse_stock_filters_to_one_branch_when_given():
    response = _get(warehouse_stock, {"sku": "TENT-2P-GRN", "branch_id": "branch-seattle"})

    assert json.loads(response.get_body()) == {"branch-seattle": 4}


def test_warehouse_stock_requires_a_sku():
    response = _get(warehouse_stock, {})

    assert response.status_code == 400


def test_warehouse_stock_returns_404_for_an_unknown_sku():
    response = _get(warehouse_stock, {"sku": "NOT-A-REAL-SKU"})

    assert response.status_code == 404


def test_shipping_eta_returns_the_eta_for_a_shipped_order():
    response = _get(shipping_eta, {"order_id": "CO-10231"})

    assert response.status_code == 200
    assert json.loads(response.get_body()) == {"eta": "2 business days"}


def test_shipping_eta_requires_an_order_id():
    response = _get(shipping_eta, {})

    assert response.status_code == 400


def test_shipping_eta_returns_404_for_an_unknown_order():
    response = _get(shipping_eta, {"order_id": "CO-00000"})

    assert response.status_code == 404
