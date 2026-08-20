"""Publishes an agent as a Foundry Agent Application, watches versions
snapshot automatically, splits traffic between a stable and a canary
version, and rolls back if the canary doesn't work out.
"""

from __future__ import annotations


def publish_first_version(agent_applications_client, *, name: str, agent_id: str):
    """Publishes the first version of an Agent Application."""
    # TODO(lab-26): call agent_applications_client.create() with name,
    # agent_id, and notes="Initial publish.".
    raise NotImplementedError("publish_first_version is not implemented yet")


def publish_new_version(agent_applications_client, app_id: str, *, agent_id: str, notes: str):
    """Publishes a new version."""
    # TODO(lab-26): call agent_applications_client.publish_version().
    raise NotImplementedError("publish_new_version is not implemented yet")


def canary_traffic_split(agent_applications_client, app_id: str, *, stable_version: int, canary_version: int, canary_percent: float):
    """Splits traffic between a stable and a canary version."""
    # TODO(lab-26): build a split dict {stable_version: 100 - canary_percent,
    # canary_version: canary_percent}, and call
    # agent_applications_client.set_traffic_split(app_id, split).
    raise NotImplementedError("canary_traffic_split is not implemented yet")


def rollback_to_version(agent_applications_client, app_id: str, *, version: int):
    """Rolls back to a prior version, sending it 100% of traffic."""
    # TODO(lab-26): call agent_applications_client.rollback().
    raise NotImplementedError("rollback_to_version is not implemented yet")


def main() -> None:
    import os

    from azure.ai.projects import AIProjectClient
    from azure.identity import DefaultAzureCredential

    endpoint = os.environ["FOUNDRY_PROJECT_ENDPOINT"]
    agent_id = os.environ["PROMPT_AGENT_ID"]
    client = AIProjectClient(endpoint=endpoint, credential=DefaultAzureCredential())

    app = publish_first_version(client.agent_applications, name="cascadia-support-app", agent_id=agent_id)
    print(f"Published {app.name} as {app.id}, version 1.")

    version_2 = publish_new_version(
        client.agent_applications, app.id, agent_id=agent_id, notes="Updated return-policy phrasing."
    )
    canary_traffic_split(
        client.agent_applications, app.id, stable_version=1, canary_version=version_2.version, canary_percent=10.0
    )
    print(f"Version {version_2.version} live at 10% traffic.")


if __name__ == "__main__":
    main()
