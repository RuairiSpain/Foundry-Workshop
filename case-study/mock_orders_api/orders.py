"""An in-memory stand-in for Cascadia's real orders and inventory system.

Labs 09 and 10 register the functions below as agent tools. The data is
fixed and deterministic on purpose, so a lab's tests can assert on exact
values instead of ranges. Lab 10 wraps `get_warehouse_stock` and
`get_shipping_eta` behind an HTTP endpoint instead of calling them
in-process — the functions themselves don't change.
"""

from __future__ import annotations

import dataclasses

_ORDERS: dict[str, dict] = {
    "CO-10231": {
        "customer_email": "maya@example.com",
        "items": [{"sku": "TENT-2P-GRN", "name": "2-Person Trail Tent, Green", "qty": 1}],
        "status": "shipped",
        "carrier": "SwiftShip",
        "tracking_number": "SS-88213",
    },
    "CO-10245": {
        "customer_email": "maya@example.com",
        "items": [{"sku": "PACK-45L-BLU", "name": "45L Daypack, Blue", "qty": 1}],
        "status": "processing",
        "carrier": None,
        "tracking_number": None,
    },
    "CO-10309": {
        "customer_email": "priya@example.com",
        "items": [{"sku": "BOOT-M-10", "name": "Trail Boot, Men's 10", "qty": 1}],
        "status": "delivered",
        "carrier": "SwiftShip",
        "tracking_number": "SS-88004",
    },
}

_WAREHOUSE_STOCK: dict[str, dict[str, int]] = {
    "TENT-2P-GRN": {"branch-seattle": 4, "branch-portland": 0, "warehouse-central": 22},
    "PACK-45L-BLU": {"branch-seattle": 0, "branch-portland": 6, "warehouse-central": 15},
    "BOOT-M-10": {"branch-seattle": 9, "branch-portland": 3, "warehouse-central": 40},
}


class OrderNotFoundError(LookupError):
    """Raised when an order ID isn't in the system."""


class SkuNotFoundError(LookupError):
    """Raised when a SKU isn't in the catalog."""


@dataclasses.dataclass
class OrderStatus:
    order_id: str
    status: str
    items: list[dict]
    carrier: str | None
    tracking_number: str | None


def get_order_status(order_id: str) -> OrderStatus:
    """Returns the status of one order.

    Raises OrderNotFoundError if `order_id` doesn't exist, so the tool
    layer can turn that into a clear message for the agent instead of a
    raw KeyError.
    """
    order = _ORDERS.get(order_id)
    if order is None:
        raise OrderNotFoundError(order_id)
    return OrderStatus(
        order_id=order_id,
        status=order["status"],
        items=order["items"],
        carrier=order["carrier"],
        tracking_number=order["tracking_number"],
    )


def list_orders_for_customer(customer_email: str) -> list[OrderStatus]:
    """Returns every order for a customer, most recent first.

    The fixture data has no order date, so "most recent first" is
    approximated by order ID, which is assigned in creation order.
    """
    matches = [
        get_order_status(order_id)
        for order_id, order in _ORDERS.items()
        if order["customer_email"] == customer_email
    ]
    return sorted(matches, key=lambda o: o.order_id, reverse=True)


def get_warehouse_stock(sku: str, branch_id: str | None = None) -> dict[str, int]:
    """Returns stock counts for a SKU, across branches or for one branch.

    Raises SkuNotFoundError if `sku` isn't in the catalog.
    """
    stock = _WAREHOUSE_STOCK.get(sku)
    if stock is None:
        raise SkuNotFoundError(sku)
    if branch_id is None:
        return dict(stock)
    return {branch_id: stock.get(branch_id, 0)}


def get_shipping_eta(order_id: str) -> str:
    """Returns a canned ETA string for a shipped order.

    Orders that haven't shipped yet return "not yet shipped" rather than
    raising, since "no ETA" is a normal, expected answer here — not an
    error condition like a missing order ID would be.
    """
    order = get_order_status(order_id)
    if order.status != "shipped":
        return "not yet shipped"
    return "2 business days"
