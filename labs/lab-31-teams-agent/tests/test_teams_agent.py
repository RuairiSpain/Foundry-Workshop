"""Tests for solution/teams_agent.py.

main() is excluded from coverage — it makes real Foundry SDK and Teams
channel calls, exercised manually against a live tenant.
"""

import pytest

from solution.teams_agent import (
    authenticate_teams_request,
    build_teams_manifest,
    format_reply_for_teams,
    handle_teams_message,
)


def test_build_teams_manifest_has_the_required_shape():
    manifest = build_teams_manifest(app_id="app-cascadia", bot_id="bot-cascadia")

    assert manifest["id"] == "app-cascadia"
    assert manifest["manifestVersion"] == "1.17"
    assert manifest["bots"] == [
        {"botId": "bot-cascadia", "scopes": ["personal"], "supportsFiles": False, "isNotificationOnly": False}
    ]
    assert manifest["name"]["short"] == "Cascadia Order Status"


def test_build_teams_manifest_accepts_a_custom_short_name():
    manifest = build_teams_manifest(app_id="app-1", bot_id="bot-1", short_name="Cascadia Bot")

    assert manifest["name"]["short"] == "Cascadia Bot"


def test_authenticate_teams_request_accepts_the_expected_tenant():
    identity = authenticate_teams_request({"tid": "tenant-cascadia"}, expected_tenant_id="tenant-cascadia")

    assert identity.get_claim_value("tid") == "tenant-cascadia"


def test_authenticate_teams_request_rejects_an_anonymous_caller():
    with pytest.raises(PermissionError, match="anonymous"):
        authenticate_teams_request({}, expected_tenant_id="tenant-cascadia")


def test_authenticate_teams_request_rejects_the_wrong_tenant():
    with pytest.raises(PermissionError, match="tenant-other"):
        authenticate_teams_request({"tid": "tenant-other"}, expected_tenant_id="tenant-cascadia")


def test_format_reply_for_teams_returns_a_message_activity():
    activity = format_reply_for_teams("Order CO-10231 shipped yesterday.")

    assert activity.type == "message"
    assert activity.text == "Order CO-10231 shipped yesterday."


def test_handle_teams_message_authenticates_then_asks_then_formats():
    calls = []

    def ask(question: str) -> str:
        calls.append(question)
        return "Order CO-10231 shipped yesterday."

    activity = handle_teams_message(
        ask,
        incoming_text="What's the status of order CO-10231?",
        claims={"tid": "tenant-cascadia"},
        expected_tenant_id="tenant-cascadia",
    )

    assert calls == ["What's the status of order CO-10231?"]
    assert activity.text == "Order CO-10231 shipped yesterday."


def test_handle_teams_message_never_asks_the_agent_when_auth_fails():
    calls = []

    def ask(question: str) -> str:
        calls.append(question)
        return "should not be reached"

    with pytest.raises(PermissionError):
        handle_teams_message(
            ask,
            incoming_text="What's the status of order CO-10231?",
            claims={"tid": "tenant-other"},
            expected_tenant_id="tenant-cascadia",
        )

    assert calls == []
