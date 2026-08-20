"""Publishes an agent as a Foundry Agent Application, watches versions
snapshot automatically, splits traffic between a stable and a canary
version, and rolls back if the canary doesn't work out.

Agent Applications have no stable typed SDK as of writing this
workshop — a real call goes through `AIProjectClient.send_request()`
against a preview REST surface. `agent_applications_client` below is
this lab's own stand-in for that surface, the same one
`case-study/testing/foundry_mocks.py`'s `FakeAgentApplicationsClient`
models for tests. See main() for the caveat spelled out inline.
"""

from __future__ import annotations


def publish_first_version(agent_applications_client, *, name: str, agent_id: str):
    """Publishes the first version of an Agent Application."""
    return agent_applications_client.create(name=name, agent_id=agent_id, notes="Initial publish.")


def publish_new_version(agent_applications_client, app_id: str, *, agent_id: str, notes: str):
    """Publishes a new version. By default, this shifts 100% of traffic
    to it immediately — canary_traffic_split() below is how you avoid
    that.
    """
    return agent_applications_client.publish_version(app_id, agent_id=agent_id, notes=notes)


def canary_traffic_split(agent_applications_client, app_id: str, *, stable_version: int, canary_version: int, canary_percent: float):
    """Splits traffic between a stable and a canary version.

    Raises ValueError (via the client) if either version doesn't exist
    on this application — the same constraint the real Portal enforces.
    """
    split = {stable_version: 100 - canary_percent, canary_version: canary_percent}
    return agent_applications_client.set_traffic_split(app_id, split)


def rollback_to_version(agent_applications_client, app_id: str, *, version: int):
    """Rolls back to a prior version, sending it 100% of traffic."""
    return agent_applications_client.rollback(app_id, to_version=version)


def main() -> None:  # pragma: no cover - real SDK wiring and CLI entry point, exercised manually
    import os

    from azure.ai.projects import AIProjectClient
    from azure.identity import DefaultAzureCredential

    endpoint = os.environ["FOUNDRY_PROJECT_ENDPOINT"]
    agent_id = os.environ["PROMPT_AGENT_ID"]
    # client.agent_applications is this lab's own stand-in — Agent
    # Applications have no stable typed SDK yet, so a real call goes
    # through client.send_request() against a preview REST surface.
    client = AIProjectClient(endpoint=endpoint, credential=DefaultAzureCredential(), allow_preview=True)

    app = publish_first_version(client.agent_applications, name="cascadia-support-app", agent_id=agent_id)
    print(f"Published {app.name} as {app.id}, version 1.")

    version_2 = publish_new_version(
        client.agent_applications, app.id, agent_id=agent_id, notes="Updated return-policy phrasing."
    )
    canary_traffic_split(
        client.agent_applications, app.id, stable_version=1, canary_version=version_2.version, canary_percent=10.0
    )
    print(f"Version {version_2.version} live at 10% traffic.")


if __name__ == "__main__":  # pragma: no cover
    main()
