"""Tests for solution/order_status_agent.py.

main() is excluded from coverage — real SDK wiring and a CLI entry
point, exercised manually, not under test.
"""

import pytest

from solution.order_status_agent import (
    ask_in_thread,
    create_order_status_agent,
    execute_tool,
)
from testing.foundry_mocks import FakeAgentsClient


def test_create_order_status_agent_registers_both_tools():
    agents_client = FakeAgentsClient()

    agent = create_order_status_agent(agents_client, model="cascadia-low-cost")

    tool_names = {tool["function"]["name"] for tool in agent.tools}
    assert tool_names == {"get_order_status", "list_orders_for_customer"}


def test_execute_tool_returns_order_status_for_a_known_order():
    result = execute_tool("get_order_status", {"order_id": "CO-10231"})

    assert result.status == "shipped"
    assert result.carrier == "SwiftShip"


def test_execute_tool_returns_an_error_dict_for_an_unknown_order():
    result = execute_tool("get_order_status", {"order_id": "CO-99999"})

    assert result == {"error": "No order found with ID CO-99999"}


def test_execute_tool_lists_orders_for_a_customer():
    result = execute_tool("list_orders_for_customer", {"customer_email": "maya@example.com"})

    assert {order.order_id for order in result} == {"CO-10231", "CO-10245"}


def test_execute_tool_raises_for_an_unregistered_tool_name():
    with pytest.raises(ValueError, match="check_the_weather"):
        execute_tool("check_the_weather", {})


def test_ask_in_thread_returns_the_agents_reply():
    agents_client = FakeAgentsClient()
    agent = create_order_status_agent(agents_client, model="cascadia-low-cost")
    thread = agents_client.threads.create()
    agents_client.script_tool_calls(agent.id, [("get_order_status", {"order_id": "CO-10231"})])
    agents_client.script_final_reply(agent.id, "Your order CO-10231 has shipped via SwiftShip.")

    reply = ask_in_thread(agents_client, thread.id, agent.id, "What's the status of order CO-10231?")

    assert reply == "Your order CO-10231 has shipped via SwiftShip."


def test_ask_in_thread_calls_the_real_tool_implementation():
    agents_client = FakeAgentsClient()
    agent = create_order_status_agent(agents_client, model="cascadia-low-cost")
    thread = agents_client.threads.create()
    agents_client.script_tool_calls(agent.id, [("get_order_status", {"order_id": "CO-10231"})])
    agents_client.script_final_reply(agent.id, "reply")

    run = agents_client.runs.create_and_process(thread.id, agent_id=agent.id, tool_executor=execute_tool)

    tool_name, call_info = run.tool_calls_made[0]
    assert tool_name == "get_order_status"
    assert call_info["result"].status == "shipped"


def test_two_turns_in_the_same_thread_both_answer_and_accumulate_history():
    agents_client = FakeAgentsClient()
    agent = create_order_status_agent(agents_client, model="cascadia-low-cost")
    thread = agents_client.threads.create()

    agents_client.script_tool_calls(agent.id, [("get_order_status", {"order_id": "CO-10231"})])
    agents_client.script_final_reply(agent.id, "Order CO-10231 has shipped.")
    reply_1 = ask_in_thread(agents_client, thread.id, agent.id, "What's the status of CO-10231?")

    agents_client.script_tool_calls(agent.id, [("get_order_status", {"order_id": "CO-10245"})])
    agents_client.script_final_reply(agent.id, "Order CO-10245 is still processing.")
    reply_2 = ask_in_thread(agents_client, thread.id, agent.id, "What about CO-10245?")

    assert reply_1 == "Order CO-10231 has shipped."
    assert reply_2 == "Order CO-10245 is still processing."
    assert len(agents_client.messages.list(thread.id)) == 4  # 2 user + 2 assistant
