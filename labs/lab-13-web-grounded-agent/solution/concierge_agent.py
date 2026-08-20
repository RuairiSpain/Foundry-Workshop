"""Builds Cascadia's trail concierge: one agent combining live web
search, the Foundry IQ knowledge base, and the Lab 11 loyalty tool from
the Toolbox — three different grounding sources on one agent.
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
    thread = agents_client.create_thread()
    agents_client.create_message(thread_id=thread.id, role="user", content=question)
    agents_client.create_and_process_run(thread_id=thread.id, agent_id=agent_id)
    return agents_client.list_messages(thread_id=thread.id)[-1].content


def main() -> None:  # pragma: no cover - real SDK wiring and CLI entry point, exercised manually
    import os

    from azure.ai.projects import AIProjectClient
    from azure.identity import DefaultAzureCredential

    endpoint = os.environ["FOUNDRY_PROJECT_ENDPOINT"]
    knowledge_base_id = os.environ["FOUNDRY_IQ_KNOWLEDGE_BASE_ID"]
    client = AIProjectClient(endpoint=endpoint, credential=DefaultAzureCredential())
    agent = build_concierge_agent(
        client.agents, model=os.environ.get("LOW_COST_DEPLOYMENT", "cascadia-low-cost"), knowledge_base_id=knowledge_base_id
    )
    reply = ask_concierge(client.agents, agent.id, "What's the trail condition on Skyline Divide this week?")
    print(reply)


if __name__ == "__main__":  # pragma: no cover
    main()
