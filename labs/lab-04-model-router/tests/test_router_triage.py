"""Tests for solution/router_triage.py.

main() is excluded from coverage — real SDK wiring and a CLI entry
point, exercised manually, not under test.
"""

from solution.router_triage import route_all, route_question, summarize_routing, triage_questions
from testing.foundry_mocks import FakeAIProjectClient


def test_triage_questions_returns_at_least_one_easy_and_one_hard_question():
    questions = triage_questions()

    assert len(questions) >= 2
    assert any(len(q) < 60 for q in questions)  # an easy, short question
    assert any(len(q) > 200 for q in questions)  # a hard, multi-part question


def test_route_question_records_the_underlying_model_not_the_deployment_name():
    client = FakeAIProjectClient()
    chat_client = client.inference.get_chat_completions_client()
    chat_client.queue_reply("60 days.", model="gpt-5-mini")

    reply = route_question(chat_client, "What is your return window?", router_deployment="cascadia-router")

    assert reply.underlying_model == "gpt-5-mini"
    assert chat_client.calls[0]["model"] == "cascadia-router"


def test_route_all_calls_once_per_question_in_order():
    client = FakeAIProjectClient()
    chat_client = client.inference.get_chat_completions_client()
    chat_client.queue_reply("reply one", model="gpt-5-mini")
    chat_client.queue_reply("reply two", model="gpt-5")

    replies = route_all(client, ["easy question", "hard question"], router_deployment="cascadia-router")

    assert [r.question for r in replies] == ["easy question", "hard question"]
    assert [r.underlying_model for r in replies] == ["gpt-5-mini", "gpt-5"]


def test_summarize_routing_counts_per_underlying_model():
    client = FakeAIProjectClient()
    chat_client = client.inference.get_chat_completions_client()
    chat_client.queue_reply("a", model="gpt-5-mini")
    chat_client.queue_reply("b", model="gpt-5-mini")
    chat_client.queue_reply("c", model="gpt-5")

    replies = route_all(client, ["q1", "q2", "q3"], router_deployment="cascadia-router")
    summary = summarize_routing(replies)

    assert summary == {"gpt-5-mini": 2, "gpt-5": 1}


def test_summarize_routing_handles_an_empty_batch():
    assert summarize_routing([]) == {}
