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


def build_project_client():
    """Builds the real AIProjectClient from environment configuration."""
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
    hint on failure.
    """
    # TODO(lab-01): get the OpenAI-shaped client from `client.get_openai_client()`.
    chat_client = None

    # TODO(lab-01): call chat_client.chat.completions.create() with
    # `model=deployment_name` and a one-message conversation asking for
    # the word "ready". Wrap the call in try/except and raise
    # SetupCheckError with a hint on failure, using `raise ... from exc`
    # to keep the original traceback.

    # TODO(lab-01): return the reply text from the response.
    raise NotImplementedError("check_connection is not implemented yet")


def main() -> None:
    client = build_project_client()
    reply = check_connection(client)
    print(f"Connected. Hub replied: {reply!r}")


if __name__ == "__main__":
    main()
