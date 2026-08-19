"""Tests for solution/function_tool_client.py.

main() is excluded from coverage — it makes a real network call,
exercised manually, not under test.
"""

import dataclasses

import pytest

from solution.function_tool_client import (
    FunctionToolError,
    call_shipping_eta,
    call_warehouse_stock,
    execute_remote_tool,
)


@dataclasses.dataclass
class FakeHttpResponse:
    status_code: int
    _body: dict | None = None
    text: str = ""

    def json(self) -> dict:
        return self._body


class FakeHttpGet:
    """Records every call and returns a scripted response, standing in
    for `requests.get` without a real network call."""

    def __init__(self, response: FakeHttpResponse):
        self.response = response
        self.calls: list[dict] = []

    def __call__(self, url: str, *, params: dict):
        self.calls.append({"url": url, "params": params})
        return self.response


@pytest.fixture(autouse=True)
def function_env(monkeypatch):
    monkeypatch.setenv("WAREHOUSE_FUNCTION_URL", "https://cascadia-functions.example.com")
    monkeypatch.setenv("WAREHOUSE_FUNCTION_KEY", "test-function-key")


def test_call_warehouse_stock_returns_the_parsed_response():
    http_get = FakeHttpGet(FakeHttpResponse(status_code=200, _body={"branch-seattle": 4}))

    result = call_warehouse_stock(http_get, "TENT-2P-GRN")

    assert result == {"branch-seattle": 4}
    assert http_get.calls[0]["url"] == "https://cascadia-functions.example.com/api/warehouse-stock"
    assert http_get.calls[0]["params"]["sku"] == "TENT-2P-GRN"
    assert http_get.calls[0]["params"]["code"] == "test-function-key"


def test_call_warehouse_stock_includes_branch_id_only_when_given():
    http_get = FakeHttpGet(FakeHttpResponse(status_code=200, _body={}))

    call_warehouse_stock(http_get, "TENT-2P-GRN")
    assert "branch_id" not in http_get.calls[0]["params"]

    call_warehouse_stock(http_get, "TENT-2P-GRN", branch_id="branch-seattle")
    assert http_get.calls[1]["params"]["branch_id"] == "branch-seattle"


def test_call_warehouse_stock_raises_on_a_non_200_response():
    http_get = FakeHttpGet(FakeHttpResponse(status_code=404, text="Unknown SKU"))

    with pytest.raises(FunctionToolError, match="404"):
        call_warehouse_stock(http_get, "NOT-A-REAL-SKU")


def test_call_shipping_eta_returns_the_eta_string():
    http_get = FakeHttpGet(FakeHttpResponse(status_code=200, _body={"eta": "2 business days"}))

    result = call_shipping_eta(http_get, "CO-10231")

    assert result == "2 business days"


def test_call_shipping_eta_raises_on_a_non_200_response():
    http_get = FakeHttpGet(FakeHttpResponse(status_code=500, text="server error"))

    with pytest.raises(FunctionToolError, match="500"):
        call_shipping_eta(http_get, "CO-10231")


def test_missing_url_env_var_raises_a_clear_error(monkeypatch):
    monkeypatch.delenv("WAREHOUSE_FUNCTION_URL", raising=False)
    http_get = FakeHttpGet(FakeHttpResponse(status_code=200, _body={}))

    with pytest.raises(FunctionToolError, match="WAREHOUSE_FUNCTION_URL"):
        call_warehouse_stock(http_get, "TENT-2P-GRN")


def test_missing_key_env_var_raises_a_clear_error(monkeypatch):
    monkeypatch.delenv("WAREHOUSE_FUNCTION_KEY", raising=False)
    http_get = FakeHttpGet(FakeHttpResponse(status_code=200, _body={}))

    with pytest.raises(FunctionToolError, match="WAREHOUSE_FUNCTION_KEY"):
        call_warehouse_stock(http_get, "TENT-2P-GRN")


def test_execute_remote_tool_dispatches_warehouse_stock():
    http_get = FakeHttpGet(FakeHttpResponse(status_code=200, _body={"branch-seattle": 4}))

    result = execute_remote_tool(http_get, "get_warehouse_stock", {"sku": "TENT-2P-GRN"})

    assert result == {"branch-seattle": 4}


def test_execute_remote_tool_dispatches_shipping_eta():
    http_get = FakeHttpGet(FakeHttpResponse(status_code=200, _body={"eta": "2 business days"}))

    result = execute_remote_tool(http_get, "get_shipping_eta", {"order_id": "CO-10231"})

    assert result == "2 business days"


def test_execute_remote_tool_raises_for_an_unregistered_tool_name():
    http_get = FakeHttpGet(FakeHttpResponse(status_code=200, _body={}))

    with pytest.raises(ValueError, match="check_the_weather"):
        execute_remote_tool(http_get, "check_the_weather", {})
