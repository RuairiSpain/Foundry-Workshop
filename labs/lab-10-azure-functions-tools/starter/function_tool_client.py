"""Calls the deployed Azure Function tools over HTTP, standing in for
the in-process functions Lab 09 called directly.
"""

from __future__ import annotations

import os


class FunctionToolError(RuntimeError):
    """Raised when a deployed tool call fails, with the HTTP status attached."""


def _function_base_url() -> str:
    base_url = os.environ.get("WAREHOUSE_FUNCTION_URL")
    if not base_url:
        raise FunctionToolError("WAREHOUSE_FUNCTION_URL is not set. See README.md step 3.")
    return base_url.rstrip("/")


def _function_key() -> str:
    key = os.environ.get("WAREHOUSE_FUNCTION_KEY")
    if not key:
        raise FunctionToolError("WAREHOUSE_FUNCTION_KEY is not set. See README.md step 3.")
    return key


def call_warehouse_stock(http_get, sku: str, branch_id: str | None = None) -> dict:
    """Calls the deployed warehouse-stock function over HTTP."""
    # TODO(lab-10): build params with "sku" and "code" (from
    # _function_key()), adding "branch_id" only when it's not None.
    # Call http_get(url, params=params), raise FunctionToolError if
    # response.status_code != 200, otherwise return response.json().
    raise NotImplementedError("call_warehouse_stock is not implemented yet")


def call_shipping_eta(http_get, order_id: str) -> str:
    """Calls the deployed shipping-eta function over HTTP."""
    # TODO(lab-10): same pattern as call_warehouse_stock(), against
    # /api/shipping-eta with an "order_id" param, returning
    # response.json()["eta"].
    raise NotImplementedError("call_shipping_eta is not implemented yet")


def execute_remote_tool(http_get, tool_name: str, args: dict):
    """Dispatches one tool call to its deployed HTTP implementation."""
    # TODO(lab-10): mirror Lab 09's execute_tool(), calling
    # call_warehouse_stock() or call_shipping_eta(), and raising
    # ValueError for any other tool_name.
    raise NotImplementedError("execute_remote_tool is not implemented yet")


def main() -> None:
    import requests

    result = call_warehouse_stock(requests.get, "TENT-2P-GRN")
    print(f"Warehouse stock: {result}")


if __name__ == "__main__":
    main()
