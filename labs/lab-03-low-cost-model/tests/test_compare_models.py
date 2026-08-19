"""Tests for solution/compare_models.py.

main() is excluded from coverage — it's real SDK wiring and a CLI entry
point, exercised manually, not under test.
"""

from solution.compare_models import run_comparison
from testing.foundry_mocks import FakeAIProjectClient


def test_run_comparison_calls_both_deployments():
    client = FakeAIProjectClient()
    chat_client = client.inference.get_chat_completions_client()
    chat_client.queue_reply("We sell outdoor gear.", model="cascadia-low-cost", total_tokens=20)
    chat_client.queue_reply("Cascadia Outfitters sells outdoor recreation gear.", model="cascadia-router", total_tokens=35)

    run_comparison(
        client, "What does Cascadia sell?", low_cost_deployment="cascadia-low-cost", router_deployment="cascadia-router"
    )

    assert [call["model"] for call in chat_client.calls] == ["cascadia-low-cost", "cascadia-router"]


def test_run_comparison_returns_both_replies():
    client = FakeAIProjectClient()
    chat_client = client.inference.get_chat_completions_client()
    chat_client.queue_reply("short answer", model="cascadia-low-cost", total_tokens=20)
    chat_client.queue_reply("longer, more detailed answer", model="cascadia-router", total_tokens=35)

    result = run_comparison(
        client, "What does Cascadia sell?", low_cost_deployment="cascadia-low-cost", router_deployment="cascadia-router"
    )

    assert result.low_cost.content == "short answer"
    assert result.low_cost.total_tokens == 20
    assert result.router.content == "longer, more detailed answer"
    assert result.router.total_tokens == 35


def test_token_difference_is_router_minus_low_cost():
    client = FakeAIProjectClient()
    chat_client = client.inference.get_chat_completions_client()
    chat_client.queue_reply("short", total_tokens=20)
    chat_client.queue_reply("long", total_tokens=50)

    result = run_comparison(
        client, "prompt", low_cost_deployment="cascadia-low-cost", router_deployment="cascadia-router"
    )

    assert result.token_difference == 30


def test_call_model_sends_the_prompt_as_a_single_user_message():
    client = FakeAIProjectClient()
    chat_client = client.inference.get_chat_completions_client()
    chat_client.queue_reply("reply one", total_tokens=10)
    chat_client.queue_reply("reply two", total_tokens=10)

    run_comparison(client, "hello world", low_cost_deployment="a", router_deployment="b")

    assert chat_client.calls[0]["messages"] == [{"role": "user", "content": "hello world"}]
