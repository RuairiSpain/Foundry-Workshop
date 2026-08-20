"""Tests for solution/mcp_server.py.

`app.run()` is excluded from coverage — it starts a real stdio server,
exercised manually, not under test. Everything else runs through
`call_tool()` directly, the same entry point a real MCP client uses,
with no transport involved.
"""

import json

import pytest

from loyalty_api.loyalty import LoyaltyLedger
from solution.mcp_server import build_server


def _result_json(result) -> dict:
    """Both tools return a dict; FastMCP serializes it as one JSON text block."""
    return json.loads(result[0].text)


@pytest.fixture
def server():
    return build_server(LoyaltyLedger())


async def test_both_tools_are_registered(server):
    tools = await server.list_tools()

    assert {tool.name for tool in tools} == {"get_loyalty_points", "redeem_loyalty_points"}


async def test_get_loyalty_points_returns_the_balance(server):
    result = await server.call_tool("get_loyalty_points", {"customer_email": "maya@example.com"})

    assert _result_json(result) == {"customer_email": "maya@example.com", "balance": 1200}


async def test_get_loyalty_points_returns_an_error_for_an_unknown_customer(server):
    result = await server.call_tool("get_loyalty_points", {"customer_email": "nobody@example.com"})

    assert _result_json(result) == {"error": "No loyalty account for nobody@example.com"}


async def test_redeem_loyalty_points_reduces_the_balance(server):
    result = await server.call_tool("redeem_loyalty_points", {"customer_email": "maya@example.com", "points": 200})

    assert _result_json(result) == {"customer_email": "maya@example.com", "redeemed": 200, "new_balance": 1000}


async def test_redeem_loyalty_points_returns_an_error_for_an_unknown_customer(server):
    result = await server.call_tool("redeem_loyalty_points", {"customer_email": "nobody@example.com", "points": 10})

    assert _result_json(result) == {"error": "No loyalty account for nobody@example.com"}


async def test_redeem_loyalty_points_returns_an_error_when_over_redeeming(server):
    result = await server.call_tool("redeem_loyalty_points", {"customer_email": "priya@example.com", "points": 9999})

    assert _result_json(result) == {"error": "priya@example.com has 340 points, cannot redeem 9999"}


async def test_redemptions_are_scoped_to_one_server_instance(server):
    """Two servers, each built with its own LoyaltyLedger, don't share state —
    the same isolation Lab 20's per-attendee Cosmos container relies on."""
    other_server = build_server(LoyaltyLedger())

    await server.call_tool("redeem_loyalty_points", {"customer_email": "maya@example.com", "points": 500})
    result = await other_server.call_tool("get_loyalty_points", {"customer_email": "maya@example.com"})

    assert _result_json(result)["balance"] == 1200
