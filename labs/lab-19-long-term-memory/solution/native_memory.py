"""Demonstrates Foundry's native long-term agent memory: a fact a
customer establishes in one thread is still available in a second,
unrelated thread — something Lab 09's thread state never gave you.

Verified against `azure-ai-agents` 1.1.0's `AgentsClient`: threads,
messages, and runs are sub-clients (`.threads`, `.messages`, `.runs`),
and `MessageRole` only has `user` and `assistant` — no `system` role
for a thread message, so remembered facts are folded into the user
message instead of sent as a separate system-role one.
"""

from __future__ import annotations


def remember_preference(memory_client, user_id: str, fact: str) -> None:
    """Stores one fact about a customer in long-term memory."""
    memory_client.remember(user_id, fact)


def recall_preferences(memory_client, user_id: str) -> list[str]:
    """Returns every fact remembered about a customer, across all threads."""
    return memory_client.recall(user_id)


def _memory_context_message(facts: list[str], *, question: str) -> str:
    """Prepends remembered facts to the question as one user message.

    This is how memory actually reaches the model: Foundry doesn't
    silently rewrite the conversation, and a thread message only comes
    in `user` or `assistant` roles — no `system` role to carry context
    separately — so remembered facts and the question travel together
    in the same message.
    """
    return f"Known customer facts: {'; '.join(facts)}\n\n{question}"


def ask_with_memory(agents_client, memory_client, agent_id: str, user_id: str, question: str) -> str:
    """Starts a fresh thread, injects remembered facts, asks one
    question, and returns the reply.

    A fresh thread every call is the point: if the answer still reflects
    facts from an earlier, unrelated thread, that's memory working, not
    thread state — a fresh thread has no history of its own.
    """
    thread = agents_client.threads.create()
    facts = recall_preferences(memory_client, user_id)
    message_content = _memory_context_message(facts, question=question) if facts else question
    agents_client.messages.create(thread.id, role="user", content=message_content)
    agents_client.runs.create_and_process(thread.id, agent_id=agent_id)
    # order="asc" is explicit, not the default — the real service
    # defaults to newest-first, which would make [-1] the oldest
    # message instead of the agent's just-added reply.
    return agents_client.messages.list(thread.id, order="asc")[-1].content


def main() -> None:  # pragma: no cover - real SDK wiring and CLI entry point, exercised manually
    import os

    from azure.ai.agents import AgentsClient
    from azure.ai.projects import AIProjectClient
    from azure.identity import DefaultAzureCredential

    endpoint = os.environ["FOUNDRY_PROJECT_ENDPOINT"]
    agent_id = os.environ["PROMPT_AGENT_ID"]
    user_id = "maya@example.com"
    # Native memory has no stable typed SDK as of writing this workshop.
    # A real call goes through AIProjectClient.send_request() against a
    # preview REST surface, not a `.memory` property — `client.memory`
    # below is this lab's own stand-in for that preview surface, the
    # same one case-study/testing/foundry_mocks.py's FakeMemoryClient
    # models for tests. Threads, messages, and runs aren't preview,
    # though — they're the real, separately-constructed AgentsClient.
    client = AIProjectClient(endpoint=endpoint, credential=DefaultAzureCredential(), allow_preview=True)
    agents_client = AgentsClient(endpoint=endpoint, credential=DefaultAzureCredential())

    remember_preference(client.memory, user_id, "Prefers boots in women's size 8.")
    reply = ask_with_memory(agents_client, client.memory, agent_id, user_id, "What boot size should I order?")
    print(reply)


if __name__ == "__main__":  # pragma: no cover
    main()
