"""Demonstrates Foundry's native long-term agent memory: a fact a
customer establishes in one thread is still available in a second,
unrelated thread — something Lab 09's thread state never gave you.
"""

from __future__ import annotations


def remember_preference(memory_client, user_id: str, fact: str) -> None:
    """Stores one fact about a customer in long-term memory."""
    memory_client.remember(user_id, fact)


def recall_preferences(memory_client, user_id: str) -> list[str]:
    """Returns every fact remembered about a customer, across all threads."""
    return memory_client.recall(user_id)


def _memory_context_message(facts: list[str]) -> str:
    """Formats remembered facts as one context line for a new thread.

    This is how memory actually reaches the model: Foundry doesn't
    silently rewrite the conversation, it hands facts to the agent the
    same way any other context would arrive.
    """
    return f"Known customer facts: {'; '.join(facts)}"


def ask_with_memory(agents_client, memory_client, agent_id: str, user_id: str, question: str) -> str:
    """Starts a fresh thread, injects remembered facts, asks one
    question, and returns the reply.

    A fresh thread every call is the point: if the answer still reflects
    facts from an earlier, unrelated thread, that's memory working, not
    thread state — a fresh thread has no history of its own.
    """
    thread = agents_client.create_thread()
    facts = recall_preferences(memory_client, user_id)
    if facts:
        agents_client.create_message(thread_id=thread.id, role="system", content=_memory_context_message(facts))
    agents_client.create_message(thread_id=thread.id, role="user", content=question)
    agents_client.create_and_process_run(thread_id=thread.id, agent_id=agent_id)
    return agents_client.list_messages(thread_id=thread.id)[-1].content


def main() -> None:  # pragma: no cover - real SDK wiring and CLI entry point, exercised manually
    import os

    from azure.ai.projects import AIProjectClient
    from azure.identity import DefaultAzureCredential

    endpoint = os.environ["FOUNDRY_PROJECT_ENDPOINT"]
    agent_id = os.environ["PROMPT_AGENT_ID"]
    user_id = "maya@example.com"
    client = AIProjectClient(endpoint=endpoint, credential=DefaultAzureCredential())

    remember_preference(client.memory, user_id, "Prefers boots in women's size 8.")
    reply = ask_with_memory(client.agents, client.memory, agent_id, user_id, "What boot size should I order?")
    print(reply)


if __name__ == "__main__":  # pragma: no cover
    main()
