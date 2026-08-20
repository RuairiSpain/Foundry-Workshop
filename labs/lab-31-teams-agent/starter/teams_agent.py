"""Packages Lab 09's order-status agent for Microsoft Teams: verifying
the caller's tenant claim before answering, and formatting the reply as
a Teams-ready Activity instead of a plain string.

Optional: requires M365 tenant admin access to actually side-load and
test this in Teams (Steps 3-4). The channel-authentication and
message-formatting logic below runs, and is fully tested, without a
live Teams tenant — Lab 09 already covered the agent and tool-calling
parts this one packages for one more channel.
"""

from __future__ import annotations

from collections.abc import Callable

from microsoft_agents.activity import Activity
from microsoft_agents.hosting.core import AuthenticationConstants, ClaimsIdentity, MessageFactory

TEAMS_MANIFEST_VERSION = "1.17"


def build_teams_manifest(*, app_id: str, bot_id: str, short_name: str = "Cascadia Order Status") -> dict:
    """Builds the Teams app manifest for the order-status agent.

    Return a dict with these top-level keys: "$schema", "manifestVersion"
    (TEAMS_MANIFEST_VERSION), "id" (app_id), "name" (a dict with "short"
    and "full"), "description" (a dict with "short" and "full"), and
    "bots" (a list with one entry: {"botId": bot_id, "scopes":
    ["personal"], "supportsFiles": False, "isNotificationOnly": False}).
    """
    # TODO: build and return the manifest dict.
    raise NotImplementedError


def authenticate_teams_request(claims: dict, *, expected_tenant_id: str) -> ClaimsIdentity:
    """Verifies the caller's tenant claim before the agent answers anything.

    Build a `ClaimsIdentity(claims=claims, authentication_type="Bearer")`.
    Raise PermissionError if `identity.claims` is empty. Read the
    tenant ID with `identity.get_claim_value(AuthenticationConstants.TENANT_ID_CLAIM)`
    and raise PermissionError if it doesn't match `expected_tenant_id`.
    Otherwise return the identity.
    """
    # TODO: authenticate the request; raise PermissionError on failure.
    raise NotImplementedError


def format_reply_for_teams(reply_text: str) -> Activity:
    """Wraps the agent's plain-text reply in a Teams-ready Activity.

    Use `MessageFactory.text()`.
    """
    # TODO: return the formatted Activity.
    raise NotImplementedError


def handle_teams_message(
    ask_order_status_agent: Callable[[str], str],
    *,
    incoming_text: str,
    claims: dict,
    expected_tenant_id: str,
) -> Activity:
    """Authenticates the caller, asks the order-status agent, and
    returns a Teams-ready reply.

    Call `authenticate_teams_request()`, then call
    `ask_order_status_agent(incoming_text)`, then
    `format_reply_for_teams()` the result.
    """
    # TODO: wire the three functions above together.
    raise NotImplementedError


def main() -> None:  # pragma: no cover - real SDK wiring, a live Teams channel, and a CLI entry point, exercised manually
    import os

    from azure.ai.agents import AgentsClient
    from azure.identity import DefaultAzureCredential

    endpoint = os.environ["FOUNDRY_PROJECT_ENDPOINT"]
    tenant_id = os.environ["M365_TENANT_ID"]
    agents_client = AgentsClient(endpoint=endpoint, credential=DefaultAzureCredential())

    from order_status_agent import ask_in_thread, create_order_status_agent  # type: ignore[import-not-found]

    agent = create_order_status_agent(agents_client, model=os.environ.get("LOW_COST_DEPLOYMENT", "cascadia-low-cost"))
    thread = agents_client.threads.create()

    def ask(question: str) -> str:
        return ask_in_thread(agents_client, thread.id, agent.id, question)

    reply = handle_teams_message(
        ask,
        incoming_text="What's the status of order CO-10231?",
        claims={"tid": tenant_id, "aud": os.environ["TEAMS_APP_ID"]},
        expected_tenant_id=tenant_id,
    )
    print(reply.text)


if __name__ == "__main__":  # pragma: no cover
    main()
