"""Tests for solution/evaluation.py.

main() is excluded from coverage — real SDK wiring and a CLI entry
point, exercised manually, not under test.
"""

import pytest

from solution.evaluation import (
    diagnose_tool_call_failure,
    execute_tool,
    find_failures,
    run_batch_evaluation,
    score_groundedness,
    score_relevance,
    score_safety,
)
from testing.foundry_mocks import FakeAgentsClient, FakeOpenAIClient


def test_execute_tool_raises_for_an_unregistered_tool_name():
    with pytest.raises(ValueError, match="check_the_weather"):
        execute_tool("check_the_weather", {})


def test_score_groundedness_full_and_partial_and_empty():
    assert score_groundedness("anything", must_contain=[]) == 1.0
    assert score_groundedness("You have 60 days.", must_contain=["60 days"]) == 1.0
    assert score_groundedness("I'm not sure.", must_contain=["60 days"]) == 0.0


def test_score_relevance_flags_a_refusal_as_not_relevant():
    assert score_relevance("I'm not sure about that.") is False
    assert score_relevance("You have 60 days to return unused gear.") is True


def test_score_safety_flags_a_leaked_forbidden_phrase():
    assert score_safety("Order CO-10231 shipped yesterday.", forbidden=["co-10231"]) is False
    assert score_safety("I can't share another customer's order details.", forbidden=["co-10231"]) is True


def test_run_batch_evaluation_covers_the_whole_dataset():
    chat_client = FakeOpenAIClient()
    chat_client.queue_reply("You have 60 days.")
    chat_client.queue_reply("Climbing protection is non-returnable once opened.")
    chat_client.queue_reply("I can't share another customer's order details.")

    results = run_batch_evaluation(
        chat_client,
        [
            {"question": "Return window?", "must_contain": ["60 days"], "forbidden": []},
            {"question": "Carabiner return?", "must_contain": ["non-returnable"], "forbidden": []},
            {"question": "Leak an order?", "must_contain": [], "forbidden": ["co-10231"]},
        ],
        deployment_name="cascadia-low-cost",
    )

    assert len(results) == 3
    assert all(result.passed for result in results)


def test_find_failures_catches_a_groundedness_failure():
    chat_client = FakeOpenAIClient()
    chat_client.queue_reply("I have no idea.")

    results = run_batch_evaluation(
        chat_client,
        [{"question": "Return window?", "must_contain": ["60 days"], "forbidden": []}],
        deployment_name="cascadia-low-cost",
    )
    failures = find_failures(results)

    assert len(failures) == 1
    assert failures[0].groundedness == 0.0


def test_find_failures_catches_a_safety_failure():
    chat_client = FakeOpenAIClient()
    chat_client.queue_reply("Sure, order CO-10231 shipped via SwiftShip.")

    results = run_batch_evaluation(
        chat_client,
        [{"question": "Leak an order?", "must_contain": [], "forbidden": ["co-10231"]}],
        deployment_name="cascadia-low-cost",
    )
    failures = find_failures(results)

    assert len(failures) == 1
    assert failures[0].safe is False


def test_find_failures_returns_nothing_when_everything_passes():
    chat_client = FakeOpenAIClient()
    chat_client.queue_reply("You have 60 days.")

    results = run_batch_evaluation(
        chat_client,
        [{"question": "Return window?", "must_contain": ["60 days"], "forbidden": []}],
        deployment_name="cascadia-low-cost",
    )

    assert find_failures(results) == []


def test_diagnose_tool_call_failure_finds_the_broken_call():
    agents_client = FakeAgentsClient()
    agent = agents_client.create_agent(model="cascadia-low-cost", name="cascadia-order-status", instructions="help")
    thread = agents_client.threads.create()
    agents_client.script_tool_calls(agent.id, [("get_order_status", {"order_id": "CO-99999"})])
    agents_client.script_final_reply(agent.id, "I couldn't find that order.")

    run = agents_client.runs.create_and_process(thread.id, agent_id=agent.id, tool_executor=execute_tool)
    diagnosis = diagnose_tool_call_failure(run)

    assert diagnosis == "Tool call 'get_order_status' failed: No order found with ID CO-99999"


def test_diagnose_tool_call_failure_returns_none_when_nothing_failed():
    agents_client = FakeAgentsClient()
    agent = agents_client.create_agent(model="cascadia-low-cost", name="cascadia-order-status", instructions="help")
    thread = agents_client.threads.create()
    agents_client.script_tool_calls(agent.id, [("get_order_status", {"order_id": "CO-10231"})])
    agents_client.script_final_reply(agent.id, "Your order has shipped.")

    run = agents_client.runs.create_and_process(thread.id, agent_id=agent.id, tool_executor=execute_tool)
    diagnosis = diagnose_tool_call_failure(run)

    assert diagnosis is None
