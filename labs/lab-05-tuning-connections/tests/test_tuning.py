"""Tests for solution/tuning.py.

main() is excluded from coverage — real SDK wiring and a CLI entry
point, exercised manually, not under test.
"""

from solution.tuning import (
    build_completion_kwargs,
    call_with_params,
    check_prompt_caching,
    sweep_temperature,
)
from testing.foundry_mocks import FakeChatCompletionsClient


def test_build_completion_kwargs_omits_seed_by_default():
    kwargs = build_completion_kwargs(temperature=0.5, top_p=0.9, max_tokens=100)

    assert kwargs == {"temperature": 0.5, "top_p": 0.9, "max_tokens": 100}


def test_build_completion_kwargs_includes_seed_when_given():
    kwargs = build_completion_kwargs(temperature=0.5, top_p=0.9, max_tokens=100, seed=42)

    assert kwargs["seed"] == 42


def test_call_with_params_forwards_parameters_to_the_client():
    chat_client = FakeChatCompletionsClient()
    chat_client.queue_reply("a reply", total_tokens=30)

    call_with_params(chat_client, "hello", deployment_name="cascadia-low-cost", temperature=0.2, max_tokens=50)

    call = chat_client.calls[0]
    assert call["model"] == "cascadia-low-cost"
    assert call["temperature"] == 0.2
    assert call["max_tokens"] == 50


def test_call_with_params_returns_a_tuned_reply():
    chat_client = FakeChatCompletionsClient()
    chat_client.queue_reply("a reply", total_tokens=30, cached_tokens=0)

    reply = call_with_params(chat_client, "hello", deployment_name="cascadia-low-cost")

    assert reply.content == "a reply"
    assert reply.total_tokens == 30
    assert reply.cached_tokens == 0


def test_sweep_temperature_calls_once_per_value_in_order():
    chat_client = FakeChatCompletionsClient()
    chat_client.queue_reply("cold reply", total_tokens=10)
    chat_client.queue_reply("warm reply", total_tokens=10)
    chat_client.queue_reply("hot reply", total_tokens=10)

    replies = sweep_temperature(chat_client, "hello", deployment_name="cascadia-low-cost", temperatures=[0.0, 0.7, 1.4])

    assert [call["temperature"] for call in chat_client.calls] == [0.0, 0.7, 1.4]
    assert [r.content for r in replies] == ["cold reply", "warm reply", "hot reply"]


def test_check_prompt_caching_reports_no_hit_when_neither_call_is_cached():
    chat_client = FakeChatCompletionsClient()
    chat_client.queue_reply("first", cached_tokens=0)
    chat_client.queue_reply("second", cached_tokens=0)

    report = check_prompt_caching(chat_client, "hello", deployment_name="cascadia-low-cost")

    assert report.cache_hit_on_second_call is False


def test_check_prompt_caching_reports_a_hit_when_the_second_call_is_cached():
    chat_client = FakeChatCompletionsClient()
    chat_client.queue_reply("first", cached_tokens=0)
    chat_client.queue_reply("second", cached_tokens=48)

    report = check_prompt_caching(chat_client, "hello", deployment_name="cascadia-low-cost")

    assert report.first_call_cached_tokens == 0
    assert report.second_call_cached_tokens == 48
    assert report.cache_hit_on_second_call is True
