"""Tests for solution/eval_gate.py.

main() is excluded from coverage — real SDK wiring and a CLI entry
point, exercised manually, not under test.
"""

import pytest

from solution.eval_gate import (
    RegressionError,
    evaluate_deployment,
    publish_if_gate_passes,
    run_evaluation_gate,
    score_reply,
)
from testing.foundry_mocks import FakeAgentApplicationsClient, FakeChatCompletionsClient


def test_score_reply_full_and_zero():
    assert score_reply("You have 60 days.", must_contain=["60 days"]) == 1.0
    assert score_reply("I'm not sure.", must_contain=["60 days"]) == 0.0


def test_score_reply_with_no_required_phrases_is_a_perfect_score():
    assert score_reply("anything", must_contain=[]) == 1.0


def test_evaluate_deployment_averages_the_dataset():
    chat_client = FakeChatCompletionsClient()
    chat_client.queue_reply("You have 60 days.")
    chat_client.queue_reply("I'm not sure.")

    score = evaluate_deployment(
        chat_client,
        deployment_name="cascadia-low-cost",
        dataset=[
            {"question": "Return window?", "must_contain": ["60 days"]},
            {"question": "Carabiner?", "must_contain": ["non-returnable"]},
        ],
    )

    assert score == 0.5


def test_gate_passes_when_candidate_matches_baseline():
    chat_client = FakeChatCompletionsClient()
    chat_client.queue_reply("You have 60 days.")  # baseline, question 1
    chat_client.queue_reply("Climbing protection is non-returnable.")  # baseline, question 2
    chat_client.queue_reply("You have 60 days.")  # candidate, question 1
    chat_client.queue_reply("Climbing protection is non-returnable.")  # candidate, question 2

    result = run_evaluation_gate(chat_client, baseline_deployment="stable", candidate_deployment="candidate")

    assert result.baseline_score == 1.0
    assert result.candidate_score == 1.0
    assert result.passed is True


def test_gate_fails_on_a_large_regression():
    chat_client = FakeChatCompletionsClient()
    chat_client.queue_reply("You have 60 days.")
    chat_client.queue_reply("Climbing protection is non-returnable.")
    chat_client.queue_reply("I'm not sure.")
    chat_client.queue_reply("I don't know.")

    result = run_evaluation_gate(chat_client, baseline_deployment="stable", candidate_deployment="candidate")

    assert result.baseline_score == 1.0
    assert result.candidate_score == 0.0
    assert result.passed is False


def test_publish_if_gate_passes_publishes_and_canaries_on_success():
    chat_client = FakeChatCompletionsClient()
    chat_client.queue_reply("You have 60 days.")
    chat_client.queue_reply("Climbing protection is non-returnable.")
    chat_client.queue_reply("You have 60 days.")
    chat_client.queue_reply("Climbing protection is non-returnable.")
    apps_client = FakeAgentApplicationsClient()
    app = apps_client.create(name="cascadia-support-app", agent_id="agent-0001")

    version = publish_if_gate_passes(
        apps_client,
        chat_client,
        app.id,
        agent_id="agent-0002",
        baseline_deployment="stable",
        candidate_deployment="candidate",
        stable_version=1,
        notes="v2",
    )

    assert version.version == 2
    assert apps_client.get(app.id).traffic_split == {1: 90.0, 2: 10.0}


def test_publish_if_gate_passes_raises_and_does_not_publish_on_regression():
    chat_client = FakeChatCompletionsClient()
    chat_client.queue_reply("You have 60 days.")
    chat_client.queue_reply("Climbing protection is non-returnable.")
    chat_client.queue_reply("I'm not sure.")
    chat_client.queue_reply("I don't know.")
    apps_client = FakeAgentApplicationsClient()
    app = apps_client.create(name="cascadia-support-app", agent_id="agent-0001")

    with pytest.raises(RegressionError, match="Regression exceeds"):
        publish_if_gate_passes(
            apps_client,
            chat_client,
            app.id,
            agent_id="agent-0002",
            baseline_deployment="stable",
            candidate_deployment="candidate",
            stable_version=1,
            notes="v2",
        )

    assert len(apps_client.get(app.id).versions) == 1
