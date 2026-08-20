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
    return agents_client.create_agent(
        model=model,
        name="cascadia-concierge",
        instructions=(
            "You help Cascadia Outfitters customers plan trips. Ground trail "
            "and policy questions in the knowledge base, use web search for "
            "live conditions and pricing, and use the loyalty tool for point "
            "balances. Don't guess when a tool can answer instead."
        ),
        tools=[WEB_SEARCH_TOOL, KNOWLEDGE_BASE_TOOL, TOOLBOX_TOOL],
        tool_resources=_tool_resources(knowledge_base_id),
    )


def ask_concierge(agents_client, agent_id: str, question: str) -> str:
    """Starts a fresh thread, asks one question, and returns the final reply."""
    thread = agents_client.threads.create()
    agents_client.messages.create(thread.id, role="user", content=question)
    agents_client.runs.create_and_process(thread.id, agent_id=agent_id)
    # order="asc" is explicit, not the default — the real service
    # defaults to newest-first, which would make [-1] the oldest
    # message instead of the agent's just-added reply.
    return agents_client.messages.list(thread.id, order="asc")[-1].content


def main() -> None:  # pragma: no cover - real SDK wiring and CLI entry point, exercised manually
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


if __name__ == "__main__":  # pragma: no cover
    main()
