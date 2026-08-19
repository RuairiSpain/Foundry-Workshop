"""Calls the deployed Azure Function tools over HTTP, standing in for
the in-process functions Lab 09 called directly.

Agent-to-function auth: the function key is read from an environment
variable and sent as a query parameter, never hardcoded — the same
pattern the AI Gateway uses for its own key in Lab 30.
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
    """Calls the deployed warehouse-stock function over HTTP.

    `http_get` is injected so tests can substitute a fake instead of
    making a real network call — the same boundary Foundry's SDK calls
    cross in every other lab, applied here to a plain HTTP dependency
    instead of the Foundry SDK.
    """
    params = {"sku": sku, "code": _function_key()}
    if branch_id is not None:
        params["branch_id"] = branch_id
    response = http_get(f"{_function_base_url()}/api/warehouse-stock", params=params)
    if response.status_code != 200:
        raise FunctionToolError(f"warehouse-stock returned {response.status_code}: {response.text}")
    return response.json()


def call_shipping_eta(http_get, order_id: str) -> str:
    """Calls the deployed shipping-eta function over HTTP."""
    params = {"order_id": order_id, "code": _function_key()}
    response = http_get(f"{_function_base_url()}/api/shipping-eta", params=params)
    if response.status_code != 200:
        raise FunctionToolError(f"shipping-eta returned {response.status_code}: {response.text}")
    return response.json()["eta"]


def execute_remote_tool(http_get, tool_name: str, args: dict):
    """Dispatches one tool call to its deployed HTTP implementation.

    The mirror image of Lab 09's execute_tool() — same tool names and
    argument shapes, a network call instead of a direct function call.
    """
    if tool_name == "get_warehouse_stock":
        return call_warehouse_stock(http_get, args["sku"], args.get("branch_id"))
    if tool_name == "get_shipping_eta":
        return call_shipping_eta(http_get, args["order_id"])
    raise ValueError(f"Unknown tool: {tool_name}")


def main() -> None:  # pragma: no cover - real network call, exercised manually
    import requests

    result = call_warehouse_stock(requests.get, "TENT-2P-GRN")
    print(f"Warehouse stock: {result}")


if __name__ == "__main__":  # pragma: no cover
    main()
