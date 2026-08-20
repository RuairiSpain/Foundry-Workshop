"""Tests for solution/verify_setup.py.

build_project_client() and main() are excluded from coverage — they're
thin wiring over the live Azure SDK and a CLI entry point, neither
meaningful to unit test. check_connection() is the lab's actual logic
and is fully covered, including its error path.
"""

import pytest

from solution.verify_setup import SetupCheckError, check_connection
from testing.foundry_mocks import FakeAIProjectClient


def test_check_connection_returns_reply_text():
    client = FakeAIProjectClient()
    client.get_openai_client().queue_reply("ready")

    result = check_connection(client, deployment_name="cascadia-router")

    assert result == "ready"


def test_check_connection_sends_the_requested_deployment_name():
    client = FakeAIProjectClient()
    chat_client = client.get_openai_client()
    chat_client.queue_reply("ready")

    check_connection(client, deployment_name="cascadia-router")

    assert chat_client.calls[0]["model"] == "cascadia-router"


def test_check_connection_wraps_failures_with_a_hint():
    client = FakeAIProjectClient()
    # No reply queued: FakeOpenAIClient.chat.completions.create() raises
    # AssertionError, standing in for any real SDK failure.

    with pytest.raises(SetupCheckError, match="cascadia-router"):
        check_connection(client, deployment_name="cascadia-router")
