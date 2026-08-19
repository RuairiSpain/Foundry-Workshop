"""Connects to the prompt agent built in Agent Builder (see README.md)
and confirms it answers a policy question correctly.
"""

from __future__ import annotations


class AgentCheckError(RuntimeError):
    """Raised when the agent doesn't answer as expected."""


def ask_agent(agents_client, agent_id: str, question: str) -> str:
    """Starts a fresh thread, asks one question, and returns the agent's
    final reply.
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

    from azure.ai.projects import AIProjectClient
    from azure.identity import DefaultAzureCredential

    endpoint = os.environ["FOUNDRY_PROJECT_ENDPOINT"]
    agent_id = os.environ["PROMPT_AGENT_ID"]
    client = AIProjectClient(endpoint=endpoint, credential=DefaultAzureCredential())
    reply = check_grounded_reply(client.agents, agent_id, "What is your return window?", must_contain="60 days")
    print(f"Agent replied: {reply}")


if __name__ == "__main__":
    main()
