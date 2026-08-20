"""Builds Cascadia's trail concierge: one agent combining live web
search, the Foundry IQ knowledge base, and the Lab 11 loyalty tool from
the Toolbox — three different grounding sources on one agent.

Verified against `azure-ai-agents` 1.1.0's `AgentsClient` for the
thread/message/run calls: they're sub-clients (`.threads`, `.messages`,
`.runs`), not flat methods on the agents client itself.
"""

from __future__ import annotations

WEB_SEARCH_TOOL = {"type": "web_search"}
KNOWLEDGE_BASE_TOOL = {"type": "knowledge_base"}
TOOLBOX_TOOL = {"type": "mcp", "server_label": "cascadia-loyalty"}


def _tool_resources(knowledge_base_id: str) -> dict:
    return {"knowledge_base": {"knowledge_base_id": knowledge_base_id}}


def build_concierge_agent(agents_client, *, model: str, knowledge_base_id: str):
    """Creates the concierge agent with all three grounding sources attached."""
    # TODO(lab-13): call agents_client.create_agent() with model, a name,
    # instructions, tools=[WEB_SEARCH_TOOL, KNOWLEDGE_BASE_TOOL, TOOLBOX_TOOL],
    # and tool_resources=_tool_resources(knowledge_base_id).
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
    agents_client = AgentsClient(endpoint=endpoint, credential=DefaultAzureCredential())
    agent = build_concierge_agent(
        agents_client, model=os.environ.get("LOW_COST_DEPLOYMENT", "cascadia-low-cost"), knowledge_base_id=knowledge_base_id
    )
    reply = ask_concierge(agents_client, agent.id, "What's the trail condition on Skyline Divide this week?")
    print(reply)


if __name__ == "__main__":
    main()
