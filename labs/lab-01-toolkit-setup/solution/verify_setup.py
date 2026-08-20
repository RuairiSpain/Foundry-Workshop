"""Confirms an attendee's Foundry project can reach the hub's shared model.

Run this after creating your project in the Toolkit (see README.md). A
successful run proves three things at once: you signed in to the right
tenant, your project was created under the instructor's hub, and your
RBAC grant on the hub resource group has propagated.
"""

from __future__ import annotations

import os


class SetupCheckError(RuntimeError):
    """Raised when the connectivity check fails, with a specific hint."""


def build_project_client():  # pragma: no cover - thin wiring over live Azure SDKs, exercised manually, not under test
    """Builds the real AIProjectClient from environment configuration.

    Kept separate from check_connection() so tests can substitute a fake
    client without touching this function at all.
    """
    from azure.ai.projects import AIProjectClient
    from azure.identity import DefaultAzureCredential

    endpoint = os.environ.get("FOUNDRY_PROJECT_ENDPOINT")
    if not endpoint:
        raise SetupCheckError(
            "FOUNDRY_PROJECT_ENDPOINT is not set. Copy it from your project's "
            "Overview page in the Toolkit and export it before running this script."
        )
    return AIProjectClient(endpoint=endpoint, credential=DefaultAzureCredential())


def check_connection(client, *, deployment_name: str = "cascadia-router") -> str:
    """Sends one chat message through the hub's shared deployment.

    Returns the reply text on success. Raises SetupCheckError with a
    hint on the two failures attendees actually hit: a wrong deployment
    name, or an RBAC grant that hasn't propagated yet.
    """
    chat_client = client.get_openai_client()
    try:
        response = chat_client.chat.completions.create(
            model=deployment_name,
            messages=[{"role": "user", "content": "Reply with the single word: ready."}],
        )
    except Exception as exc:
        raise SetupCheckError(
            f"Could not reach deployment {deployment_name!r}. Confirm the hub's router "
            "is deployed and that your RBAC grant has propagated — that can take a "
            "few minutes after provisioning."
        ) from exc
    return response.choices[0].message.content


def main() -> None:  # pragma: no cover - thin CLI entry point, exercised manually, not under test
    client = build_project_client()
    reply = check_connection(client)
    print(f"Connected. Hub replied: {reply!r}")


if __name__ == "__main__":  # pragma: no cover
    main()
