"""Tests for solution/concierge_agent.py.

main() is excluded from coverage — real SDK wiring and a CLI entry
point, exercised manually, not under test.
"""

from solution.concierge_agent import ask_concierge, build_concierge_agent
from testing.foundry_mocks import FakeAgentsClient


def test_build_concierge_agent_attaches_all_three_tool_types():
    agents_client = FakeAgentsClient()

    agent = build_concierge_agent(
        agents_client, model="cascadia-low-cost", knowledge_base_id="kb-0001", bing_connection_id="conn-0001"
    )

    tool_types = {tool["type"] for tool in agent.tools}
    assert tool_types == {"bing_grounding", "knowledge_base", "mcp"}


def test_build_concierge_agent_attaches_the_right_knowledge_base():
    agents_client = FakeAgentsClient()

    agent = build_concierge_agent(
        agents_client, model="cascadia-low-cost", knowledge_base_id="kb-0001", bing_connection_id="conn-0001"
    )

    assert agent.tool_resources == {"knowledge_base": {"knowledge_base_id": "kb-0001"}}


def test_build_concierge_agent_references_the_loyalty_toolbox_server():
    agents_client = FakeAgentsClient()

    agent = build_concierge_agent(
        agents_client, model="cascadia-low-cost", knowledge_base_id="kb-0001", bing_connection_id="conn-0001"
    )

    mcp_tool = next(tool for tool in agent.tools if tool["type"] == "mcp")
    assert mcp_tool["server_label"] == "cascadia-loyalty"


def test_build_concierge_agent_wires_the_bing_connection_id():
    agents_client = FakeAgentsClient()

    agent = build_concierge_agent(
        agents_client, model="cascadia-low-cost", knowledge_base_id="kb-0001", bing_connection_id="conn-0001"
    )

    bing_tool = next(tool for tool in agent.tools if tool["type"] == "bing_grounding")
    assert bing_tool["bing_grounding"]["search_configurations"][0]["connection_id"] == "conn-0001"


def test_ask_concierge_returns_the_agents_reply():
    agents_client = FakeAgentsClient()
    agent = build_concierge_agent(
        agents_client, model="cascadia-low-cost", knowledge_base_id="kb-0001", bing_connection_id="conn-0001"
    )
    agents_client.script_final_reply(agent.id, "Skyline Divide is clear and dry this week.")

    reply = ask_concierge(agents_client, agent.id, "What's the trail condition on Skyline Divide?")

    assert reply == "Skyline Divide is clear and dry this week."
