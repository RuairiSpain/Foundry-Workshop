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
    # TODO(lab-19): call memory_client.remember(user_id, fact).
    raise NotImplementedError("remember_preference is not implemented yet")


def recall_preferences(memory_client, user_id: str) -> list[str]:
    """Returns every fact remembered about a customer, across all threads."""
    # TODO(lab-19): call memory_client.recall(user_id) and return it.
    raise NotImplementedError("recall_preferences is not implemented yet")


def _memory_context_message(facts: list[str], *, question: str) -> str:
    """Prepends remembered facts to the question as one user message."""
    return f"Known customer facts: {'; '.join(facts)}\n\n{question}"


def ask_with_memory(agents_client, memory_client, agent_id: str, user_id: str, question: str) -> str:
    """Starts a fresh thread, injects remembered facts, asks one
    question, and returns the reply.

    Use `agents_client.threads.create()`. Call `recall_preferences()`;
    if any facts come back, build the message content with
    `_memory_context_message(facts, question=question)`, otherwise use
    `question` as-is. Add it as a user message with
    `agents_client.messages.create(thread.id, role="user",
    content=...)`, process a run with
    `agents_client.runs.create_and_process(thread.id, agent_id=)`, and
    return the last message's content from
    `agents_client.messages.list(thread.id, order="asc")` — pass
    `order="asc"` explicitly, since the real service defaults to
    newest-first.
    """
    # TODO(lab-19): implement ask_with_memory as described above.
    raise NotImplementedError("ask_with_memory is not implemented yet")


def main() -> None:
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


if __name__ == "__main__":
    main()
