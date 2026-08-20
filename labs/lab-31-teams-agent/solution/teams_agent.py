"""Packages Lab 09's order-status agent for Microsoft Teams: verifying
the caller's tenant claim before answering, and formatting the reply as
a Teams-ready Activity instead of a plain string.

Optional: requires M365 tenant admin access to actually side-load and
test this in Teams (Steps 3-4). The channel-authentication and
message-formatting logic below runs, and is fully tested, without a
live Teams tenant — Lab 09 already covered the agent and tool-calling
parts this one packages for one more channel.

Verified against `microsoft-agents-hosting-core` 1.4.0's
`ClaimsIdentity` and `MessageFactory`, as of writing this workshop.
"""

from __future__ import annotations

from collections.abc import Callable

from microsoft_agents.activity import Activity
from microsoft_agents.hosting.core import AuthenticationConstants, ClaimsIdentity, MessageFactory

TEAMS_MANIFEST_VERSION = "1.17"


def build_teams_manifest(*, app_id: str, bot_id: str, short_name: str = "Cascadia Order Status") -> dict:
    """Builds the Teams app manifest for the order-status agent.

    This is the `manifest.json` a Teams app package ships — the same
    fields the M365 Agents Toolkit's packaging step validates, trimmed
    to what this lab exercises.
    """
    return {
        "$schema": (
            f"https://developer.microsoft.com/en-us/json-schemas/teams/v{TEAMS_MANIFEST_VERSION}/"
            "MicrosoftTeams.schema.json"
        ),
        "manifestVersion": TEAMS_MANIFEST_VERSION,
        "id": app_id,
        "name": {"short": short_name, "full": "Cascadia Outfitters Order Status"},
        "description": {
            "short": "Check a Cascadia order's status from Teams.",
            "full": "Ask about any Cascadia Outfitters order without leaving Teams.",
        },
        "bots": [{"botId": bot_id, "scopes": ["personal"], "supportsFiles": False, "isNotificationOnly": False}],
    }


def authenticate_teams_request(claims: dict, *, expected_tenant_id: str) -> ClaimsIdentity:
    """Verifies the caller's tenant claim before the agent answers anything.

    Real channel authentication verifies a signed JWT's signature
    against Teams' JWKS endpoint before this point — that's what
    `JwtTokenValidator.validate_token()` does. This function models the
    step after: checking the identity actually carries claims (an
    unauthenticated caller has none) and that those claims are for the
    tenant this deployment serves. Raises PermissionError for either
    failure, so a caller can't mistake a rejected identity for an
    authenticated one.
    """
    identity = ClaimsIdentity(claims=claims, authentication_type="Bearer")
    if not identity.claims:
        raise PermissionError("Teams request carried no claims — rejecting anonymous caller")
    tenant_id = identity.get_claim_value(AuthenticationConstants.TENANT_ID_CLAIM)
    if tenant_id != expected_tenant_id:
        raise PermissionError(f"Teams request is from tenant {tenant_id!r}, expected {expected_tenant_id!r}")
    return identity


def format_reply_for_teams(reply_text: str) -> Activity:
    """Wraps the agent's plain-text reply in a Teams-ready Activity."""
    return MessageFactory.text(reply_text)


def handle_teams_message(
    ask_order_status_agent: Callable[[str], str],
    *,
    incoming_text: str,
    claims: dict,
    expected_tenant_id: str,
) -> Activity:
    """Authenticates the caller, asks the order-status agent, and
    returns a Teams-ready reply.

    `ask_order_status_agent` is Lab 09's `ask_in_thread`, already bound
    to a client, thread, and agent — this function doesn't rebuild the
    agent, it packages the existing one for one more channel.
    """
    authenticate_teams_request(claims, expected_tenant_id=expected_tenant_id)
    reply_text = ask_order_status_agent(incoming_text)
    return format_reply_for_teams(reply_text)


def main() -> None:  # pragma: no cover - real SDK wiring, a live Teams channel, and a CLI entry point, exercised manually
    import os

    from azure.ai.projects import AIProjectClient
    from azure.identity import DefaultAzureCredential

    endpoint = os.environ["FOUNDRY_PROJECT_ENDPOINT"]
    tenant_id = os.environ["M365_TENANT_ID"]
    client = AIProjectClient(endpoint=endpoint, credential=DefaultAzureCredential())

    # Lab 09 built this agent and thread; a Teams-hosted deployment
    # would keep one thread per Teams conversation instead of one
    # global thread, using `TurnContext.activity.conversation.id` as
    # the key.
    from order_status_agent import ask_in_thread, create_order_status_agent  # type: ignore[import-not-found]

    agent = create_order_status_agent(client.agents, model=os.environ.get("LOW_COST_DEPLOYMENT", "cascadia-low-cost"))
    thread = client.agents.create_thread()

    def ask(question: str) -> str:
        return ask_in_thread(client.agents, thread.id, agent.id, question)

    reply = handle_teams_message(
        ask,
        incoming_text="What's the status of order CO-10231?",
        claims={"tid": tenant_id, "aud": os.environ["TEAMS_APP_ID"]},
        expected_tenant_id=tenant_id,
    )
    print(reply.text)


if __name__ == "__main__":  # pragma: no cover
    main()
