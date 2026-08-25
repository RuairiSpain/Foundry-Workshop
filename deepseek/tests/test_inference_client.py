"""Token-usage normalization, streaming TTFT, non-streaming latency,
and missing-usage-field handling (spec 2.13). Uses fake SDK objects —
no real network calls.
"""

from __future__ import annotations

import time

from src.client_factory import ModelClient
from src.inference_client import build_messages, execute_attempt
from tests.fakes import FakeCompletionResponse, FakeStreamChunk, FakeUsage, make_http_response_error, make_openai_status_error


def _client(config, backend, complete_return=None, stream_iterable=None):
    class FakeSdk:
        def complete(self, **kwargs):
            if stream_iterable is not None:
                return iter(stream_iterable)
            return complete_return

        class _Chat:
            class _Completions:
                def create(inner_self, **kwargs):
                    if kwargs.get("stream") and stream_iterable is not None:
                        return iter(stream_iterable)
                    return complete_return

            completions = _Completions()

        chat = _Chat()

    return ModelClient(config=config, backend=backend, client=FakeSdk())


def test_build_messages_is_fresh_every_time():
    messages = build_messages(system_instruction="sys", user_prompt="hi")
    assert messages == [{"role": "system", "content": "sys"}, {"role": "user", "content": "hi"}]


def test_non_streaming_azure_openai_normalizes_usage_and_ttft_is_none(azure_openai_config):
    usage = FakeUsage(prompt_tokens=100, completion_tokens=20, cached_tokens=30, reasoning_tokens=5)
    response = FakeCompletionResponse(id="req-1", content="hello", usage=usage)
    client = _client(azure_openai_config, "azure-openai", complete_return=response)

    result = execute_attempt(
        client, build_messages(system_instruction="s", user_prompt="u"), max_output_tokens=50, streaming=False, temperature=0, top_p=1, seed=1
    )

    assert result.succeeded
    assert result.usage.input_tokens == 100
    assert result.usage.output_tokens == 20
    assert result.usage.cached_input_tokens == 30
    assert result.usage.reasoning_tokens == 5
    assert result.usage.total_tokens == 120
    assert result.content == "hello"
    assert result.request_id == "req-1"
    # Spec 2.8: non-streaming must have a null TTFT and generation_time,
    # never a value copied from total latency.
    assert result.time_to_first_token_ms is None
    assert result.generation_time_ms is None
    assert result.client_latency_ms is not None and result.client_latency_ms >= 0


def test_non_streaming_deepseek_has_no_cached_or_reasoning_tokens(deepseek_config):
    usage = FakeUsage(prompt_tokens=40, completion_tokens=10)
    response = FakeCompletionResponse(content="hi", usage=usage)
    client = _client(deepseek_config, "azure-ai-inference", complete_return=response)

    result = execute_attempt(
        client, build_messages(system_instruction="s", user_prompt="u"), max_output_tokens=50, streaming=False, temperature=0, top_p=1, seed=1
    )

    assert result.usage.input_tokens == 40
    assert result.usage.output_tokens == 10
    # These fields are "not returned by this provider" (None), not "0".
    assert result.usage.cached_input_tokens is None
    assert result.usage.reasoning_tokens is None


def test_missing_usage_entirely_leaves_all_token_fields_none(deepseek_config):
    response = FakeCompletionResponse(content="hi", usage=None)
    client = _client(deepseek_config, "azure-ai-inference", complete_return=response)

    result = execute_attempt(
        client, build_messages(system_instruction="s", user_prompt="u"), max_output_tokens=50, streaming=False, temperature=0, top_p=1, seed=1
    )

    assert result.succeeded
    assert result.usage.input_tokens is None
    assert result.usage.output_tokens is None
    assert result.usage.total_tokens is None
    assert result.output_tokens_per_second is None


def test_streaming_computes_ttft_and_generation_time_from_content_tokens(azure_openai_config):
    def chunks():
        yield FakeStreamChunk(content="Hel")
        time.sleep(0.005)
        yield FakeStreamChunk(content="lo")
        time.sleep(0.005)
        yield FakeStreamChunk(finish_reason="stop")
        yield FakeStreamChunk(usage=FakeUsage(prompt_tokens=8, completion_tokens=3))

    client = _client(azure_openai_config, "azure-openai", stream_iterable=list(chunks()))

    result = execute_attempt(
        client, build_messages(system_instruction="s", user_prompt="u"), max_output_tokens=50, streaming=True, temperature=0, top_p=1, seed=1
    )

    assert result.succeeded
    assert result.content == "Hello"
    assert result.finish_reason == "stop"
    assert result.usage.output_tokens == 3
    assert result.time_to_first_token_ms is not None and result.time_to_first_token_ms > 0
    assert result.generation_time_ms is not None and result.generation_time_ms > 0
    # Time to first content token must be strictly less than total latency.
    assert result.time_to_first_token_ms < result.client_latency_ms
    assert result.output_tokens_per_second is not None


def test_streaming_with_no_usage_chunk_leaves_usage_empty(deepseek_config):
    chunks = [FakeStreamChunk(content="hi"), FakeStreamChunk(finish_reason="stop")]
    client = _client(deepseek_config, "azure-ai-inference", stream_iterable=chunks)

    result = execute_attempt(
        client, build_messages(system_instruction="s", user_prompt="u"), max_output_tokens=50, streaming=True, temperature=0, top_p=1, seed=1
    )

    assert result.succeeded
    assert result.usage.output_tokens is None
    assert result.output_tokens_per_second is None  # no output_tokens to divide by


def test_unsupported_parameters_are_not_sent_when_disabled(azure_openai_config):
    import dataclasses

    config = dataclasses.replace(azure_openai_config, supports_temperature=False, supports_top_p=False, supports_seed=False)
    captured_kwargs = {}

    class FakeSdk:
        class _Chat:
            class _Completions:
                def create(inner_self, **kwargs):
                    captured_kwargs.update(kwargs)
                    return FakeCompletionResponse(content="ok", usage=FakeUsage(prompt_tokens=1, completion_tokens=1))

            completions = _Completions()

        chat = _Chat()

    client = ModelClient(config=config, backend="azure-openai", client=FakeSdk())
    execute_attempt(
        client, build_messages(system_instruction="s", user_prompt="u"), max_output_tokens=50, streaming=False, temperature=0.9, top_p=0.5, seed=7
    )

    assert "temperature" not in captured_kwargs
    assert "top_p" not in captured_kwargs
    assert "seed" not in captured_kwargs
    assert captured_kwargs["max_completion_tokens"] == 50


# --- exception classification -----------------------------------------------


def test_throttled_response_is_a_retryable_failure(deepseek_config):
    class FakeSdk:
        def complete(self, **kwargs):
            raise make_http_response_error(429, "throttled")

    client = ModelClient(config=deepseek_config, backend="azure-ai-inference", client=FakeSdk())
    result = execute_attempt(
        client, build_messages(system_instruction="s", user_prompt="u"), max_output_tokens=50, streaming=False, temperature=0, top_p=1, seed=1
    )

    assert not result.succeeded
    assert result.http_status == 429
    assert result.error_type == "throttled"
    assert result.is_retryable_failure


def test_bad_request_is_not_a_retryable_failure(azure_openai_config):
    class FakeSdk:
        class _Chat:
            class _Completions:
                def create(inner_self, **kwargs):
                    raise make_openai_status_error(400, "bad request")

            completions = _Completions()

        chat = _Chat()

    client = ModelClient(config=azure_openai_config, backend="azure-openai", client=FakeSdk())
    result = execute_attempt(
        client, build_messages(system_instruction="s", user_prompt="u"), max_output_tokens=50, streaming=False, temperature=0, top_p=1, seed=1
    )

    assert not result.succeeded
    assert result.http_status == 400
    assert result.error_type == "client_error"
    assert not result.is_retryable_failure


def test_execute_attempt_never_raises_for_an_unexpected_exception(deepseek_config):
    class FakeSdk:
        def complete(self, **kwargs):
            raise RuntimeError("something broke")

    client = ModelClient(config=deepseek_config, backend="azure-ai-inference", client=FakeSdk())
    result = execute_attempt(
        client, build_messages(system_instruction="s", user_prompt="u"), max_output_tokens=50, streaming=False, temperature=0, top_p=1, seed=1
    )

    assert not result.succeeded
    assert result.error_type == "unexpected_error"
    assert result.http_status is None
