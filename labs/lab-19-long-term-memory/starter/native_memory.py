"""Demonstrates Foundry's native long-term agent memory: a fact a
customer establishes in one thread is still available in a second,
unrelated thread — something Lab 09's thread state never gave you.
"""

from __future__ import annotations


def remember_preference(memory_client, user_id: str, fact: str) -> None:
    """Stores one fact about a customer in long-term memory."""
    # TODO(lab-19): call memory_client.remember(user_id, fact).
    raise NotImplementedError("remember_preference is not implemented yet")


def recall_preferences(memory_client, user_id: str) -> list[str]:
    """Returns every fact remembered about a customer, across all threads."""
    # TODO(lab-19): call memory_client.recall(user_id) and return it.
    raise NotImplementedError("recall_preferences is not implemented yet")


def _memory_context_message(facts: list[str]) -> str:
    """Formats remembered facts as one context line for a new thread."""
    return f"Known customer facts: {'; '.join(facts)}"


def ask_with_memory(agents_client, memory_client, agent_id: str, user_id: str, question: str) -> str:
    """Starts a fresh thread, injects remembered facts, asks one
    question, and returns the reply.
    """
    # TODO(lab-19): create a thread. Call recall_preferences(); if any
    # facts come back, add a system message with
    # _memory_context_message(facts). Add the user's question as a user
    # message, process a run, and return the last message's content.
    raise NotImplementedError("ask_with_memory is not implemented yet")


def main() -> None:
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


if __name__ == "__main__":
    main()
