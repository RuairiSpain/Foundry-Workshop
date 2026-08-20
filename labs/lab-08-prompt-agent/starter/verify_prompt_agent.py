"""Connects to the prompt agent built in Agent Builder (see README.md)
and confirms it answers a policy question correctly.

Verified against `azure-ai-agents` 1.1.0's `AgentsClient`: threads,
messages, and runs are sub-clients (`.threads`, `.messages`, `.runs`),
not flat methods on the agents client itself.
"""

from __future__ import annotations


class AgentCheckError(RuntimeError):
    """Raised when the agent doesn't answer as expected."""


def ask_agent(agents_client, agent_id: str, question: str) -> str:
    """Starts a fresh thread, asks one question, and returns the agent's
    final reply.

    Use `agents_client.threads.create()`,
    `agents_client.messages.create(thread.id, role=, content=)`,
    `agents_client.runs.create_and_process(thread.id, agent_id=)`, and
    `agents_client.messages.list(thread.id, order="asc")` — pass
    `order="asc"` explicitly, since the real service defaults to
    newest-first.
    """
    # TODO(lab-08): create a thread, add a user message with `question`,
    # process a run for `agent_id`, then return the last message's content.
    raise NotImplementedError("ask_agent is not implemented yet")


def check_grounded_reply(agents_client, agent_id: str, question: str, *, must_contain: str) -> str:
    """Asks a question and raises AgentCheckError if the reply doesn't
    mention `must_contain`.
    """
    # TODO(lab-08): call ask_agent(), and raise AgentCheckError with a
    # helpful hint (case-insensitively) if must_contain isn't in the reply.
    # Otherwise return the reply.
    raise NotImplementedError("check_grounded_reply is not implemented yet")


def main() -> None:
    import os

    from azure.ai.agents import AgentsClient
    from azure.identity import DefaultAzureCredential

    endpoint = os.environ["FOUNDRY_PROJECT_ENDPOINT"]
    agent_id = os.environ["PROMPT_AGENT_ID"]
    agents_client = AgentsClient(endpoint=endpoint, credential=DefaultAzureCredential())
    reply = check_grounded_reply(agents_client, agent_id, "What is your return window?", must_contain="60 days")
    print(f"Agent replied: {reply}")


if __name__ == "__main__":
    main()
