"""Connects to the prompt agent built in Agent Builder (see README.md)
and confirms it answers a policy question correctly.

This agent is built entirely in the Toolkit, no-code — this script
exists to prove it works, the same role Lab 01's verify_setup.py played
for your project.
"""

from __future__ import annotations


class AgentCheckError(RuntimeError):
    """Raised when the agent doesn't answer as expected."""


def ask_agent(agents_client, agent_id: str, question: str) -> str:
    """Starts a fresh thread, asks one question, and returns the agent's
    final reply.

    A fresh thread per question keeps this check independent of any
    conversation history — exactly what Lab 09's classic agent adds on
    purpose, and what this lab deliberately doesn't need yet.
    """
    thread = agents_client.create_thread()
    agents_client.create_message(thread_id=thread.id, role="user", content=question)
    agents_client.create_and_process_run(thread_id=thread.id, agent_id=agent_id)
    messages = agents_client.list_messages(thread_id=thread.id)
    return messages[-1].content


def check_grounded_reply(agents_client, agent_id: str, question: str, *, must_contain: str) -> str:
    """Asks a question and raises AgentCheckError if the reply doesn't
    mention `must_contain` — a cheap proxy for "the knowledge base
    actually grounded this answer" without asserting on exact wording.
    """
    reply = ask_agent(agents_client, agent_id, question)
    if must_contain.lower() not in reply.lower():
        raise AgentCheckError(
            f"Reply did not mention {must_contain!r}. Confirm the knowledge base "
            f"is attached to the agent in Agent Builder. Reply was: {reply!r}"
        )
    return reply


def main() -> None:  # pragma: no cover - real SDK wiring and CLI entry point, exercised manually
    import os

    from azure.ai.projects import AIProjectClient
    from azure.identity import DefaultAzureCredential

    endpoint = os.environ["FOUNDRY_PROJECT_ENDPOINT"]
    agent_id = os.environ["PROMPT_AGENT_ID"]
    client = AIProjectClient(endpoint=endpoint, credential=DefaultAzureCredential())
    reply = check_grounded_reply(client.agents, agent_id, "What is your return window?", must_contain="60 days")
    print(f"Agent replied: {reply}")


if __name__ == "__main__":  # pragma: no cover
    main()
