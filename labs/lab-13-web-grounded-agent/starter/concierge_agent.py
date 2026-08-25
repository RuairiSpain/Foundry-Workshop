"""Builds Cascadia's trail concierge: one agent combining live web
search, the Foundry IQ knowledge base, and the Lab 11 loyalty tool from
the Toolbox — three different grounding sources on one agent.

Verified against `azure-ai-agents` 1.1.0's `AgentsClient` for the
thread/message/run calls: they're sub-clients (`.threads`, `.messages`,
`.runs`), not flat methods on the agents client itself. Also verified
`build_web_search_tool()` below against `azure.ai.agents.models`: the
web-search grounding tool's real, stable `type` string is
"bing_grounding" — a bare `{"type": "web_search"}` isn't a tool the
real service recognizes, so we build it with the SDK's own
`BingGroundingTool` instead of hand-writing that dict. Foundry IQ
knowledge bases and MCP Toolbox servers have no such stable, typed tool
definition yet — see the caveat on `KNOWLEDGE_BASE_TOOL` and
`TOOLBOX_TOOL` below.
"""

from __future__ import annotations

from azure.ai.agents.models import BingGroundingTool


def build_web_search_tool(connection_id: str) -> dict:
    """Builds the real `bing_grounding` tool definition for live web search.

    `connection_id` is the Bing grounding connection's full resource ID
    in your Foundry project (Foundry Portal > Management center >
    Connections > your Bing connection > see resource ID) — there's no
    SDK call to create one; it's provisioned the same way Lab 11's
    Toolbox server registration is, outside this repo.
    """
    return BingGroundingTool(connection_id=connection_id).definitions[0]


# Foundry IQ knowledge bases and MCP Toolbox servers have no stable,
# typed tool definition in `azure-ai-agents` 1.1.0 as of writing this
# workshop — these two dicts show the request shape the service expects
# today, the same "preview REST surface, no typed SDK yet" caveat Lab
# 07's `foundry_iq.py` documents for `{"type": "knowledge_base"}`. Check
# current Foundry docs for the live tool-type names before running this
# against a real project.
KNOWLEDGE_BASE_TOOL = {"type": "knowledge_base"}
TOOLBOX_TOOL = {"type": "mcp", "server_label": "cascadia-loyalty"}


def _tool_resources(knowledge_base_id: str) -> dict:
    return {"knowledge_base": {"knowledge_base_id": knowledge_base_id}}


def build_concierge_agent(agents_client, *, model: str, knowledge_base_id: str, bing_connection_id: str):
    """Creates the concierge agent with all three grounding sources attached."""
    # TODO(lab-13): call agents_client.create_agent() with model, a name,
    # instructions, tools=[build_web_search_tool(bing_connection_id),
    # KNOWLEDGE_BASE_TOOL, TOOLBOX_TOOL], and
    # tool_resources=_tool_resources(knowledge_base_id).
    raise NotImplementedError("build_concierge_agent is not implemented yet")


def ask_concierge(agents_client, agent_id: str, question: str) -> str:
    """Starts a fresh thread, asks one question, and returns the final reply.

    Use `agents_client.threads.create()`,
    `agents_client.messages.create(thread.id, role=, content=)`,
    `agents_client.runs.create_and_process(thread.id, agent_id=)`, and
    `agents_client.messages.list(thread.id, order="asc")` — pass
    `order="asc"` explicitly, since the real service defaults to
    newest-first.
    """
    # TODO(lab-13): create a thread, add a user message, process a run,
    # and return the last message's content.
    raise NotImplementedError("ask_concierge is not implemented yet")


def main() -> None:
    import os

    from azure.ai.agents import AgentsClient
    from azure.identity import DefaultAzureCredential

    endpoint = os.environ["FOUNDRY_PROJECT_ENDPOINT"]
    knowledge_base_id = os.environ["FOUNDRY_IQ_KNOWLEDGE_BASE_ID"]
    bing_connection_id = os.environ["BING_CONNECTION_ID"]
    agents_client = AgentsClient(endpoint=endpoint, credential=DefaultAzureCredential())
    agent = build_concierge_agent(
        agents_client,
        model=os.environ.get("LOW_COST_DEPLOYMENT", "cascadia-low-cost"),
        knowledge_base_id=knowledge_base_id,
        bing_connection_id=bing_connection_id,
    )
    reply = ask_concierge(agents_client, agent.id, "What's the trail condition on Skyline Divide this week?")
    print(reply)


if __name__ == "__main__":
    main()
