"""Executes one physical inference attempt against a model deployment
and measures it.

This module makes exactly one attempt per call — it never retries.
Retry/backoff policy lives in `benchmark_runner.py`, which loops calling
`execute_attempt()` and decides whether `AttemptResult.is_retryable_failure`
warrants another try. Keeping the single HTTP attempt and the retry
policy in separate modules is what lets each be unit tested without the
other (spec 2.13 lists "retry behavior" and "streaming TTFT calculation"
as separate test targets).

Latency definitions (spec 2.8), all measured with `time.monotonic()` so
wall-clock adjustments never skew a measurement:
  - client_latency_ms: before the SDK call to receipt of the final
    response (last streamed chunk, or the single non-streaming response).
  - time_to_first_token_ms: before the SDK call to receipt of the first
    streamed content token. Always None for non-streaming requests — the
    metric doesn't apply, so it isn't backfilled from total latency.
  - generation_time_ms: first streamed content token to the last one.
    Always None for non-streaming requests, for the same reason.
"""

from __future__ import annotations

import dataclasses
import datetime as dt
import time
from typing import Optional

from .client_factory import ModelClient
from .models import UsageInfo

RETRYABLE_ERROR_TYPES = {"throttled", "timeout", "server_error", "connection_error"}


@dataclasses.dataclass
class AttemptResult:
    started_at_utc: str
    completed_at_utc: str
    request_id: Optional[str]
    http_status: Optional[int]
    usage: UsageInfo
    content: Optional[str]
    finish_reason: Optional[str]
    client_latency_ms: Optional[float]
    time_to_first_token_ms: Optional[float]
    generation_time_ms: Optional[float]
    output_tokens_per_second: Optional[float]
    error_type: Optional[str] = None
    error_message: Optional[str] = None

    @property
    def succeeded(self) -> bool:
        return self.error_type is None

    @property
    def is_retryable_failure(self) -> bool:
        return self.error_type in RETRYABLE_ERROR_TYPES


def _utcnow_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def build_messages(*, system_instruction: str, user_prompt: str) -> list[dict]:
    """A single fixed system instruction plus a single fresh user
    message (spec 2.5) — no history is ever carried between prompts.
    """
    return [
        {"role": "system", "content": system_instruction},
        {"role": "user", "content": user_prompt},
    ]


def execute_attempt(
    model_client: ModelClient,
    messages: list[dict],
    *,
    max_output_tokens: int,
    streaming: bool,
    temperature: float,
    top_p: float,
    seed: Optional[int],
) -> AttemptResult:
    """Makes one physical call and measures it. Never raises for an
    HTTP-level failure (429, 5xx, timeout, ...) — those come back as a
    failed AttemptResult so the caller can decide whether to retry.
    Only a genuine bug in this function itself would propagate as an
    exception.
    """
    started_at_utc = _utcnow_iso()
    start = time.monotonic()
    try:
        if model_client.backend == "azure-openai":
            result = _execute_azure_openai(
                model_client,
                messages,
                max_output_tokens=max_output_tokens,
                streaming=streaming,
                temperature=temperature,
                top_p=top_p,
                seed=seed,
                start=start,
            )
        else:
            result = _execute_azure_ai_inference(
                model_client,
                messages,
                max_output_tokens=max_output_tokens,
                streaming=streaming,
                temperature=temperature,
                top_p=top_p,
                seed=seed,
                start=start,
            )
    except Exception as exc:  # noqa: BLE001 - classified below, never re-raised
        http_status, error_type, error_message = _classify_exception(exc)
        return AttemptResult(
            started_at_utc=started_at_utc,
            completed_at_utc=_utcnow_iso(),
            request_id=None,
            http_status=http_status,
            usage=UsageInfo(),
            content=None,
            finish_reason=None,
            client_latency_ms=(time.monotonic() - start) * 1000,
            time_to_first_token_ms=None,
            generation_time_ms=None,
            output_tokens_per_second=None,
            error_type=error_type,
            error_message=error_message,
        )

    return AttemptResult(
        started_at_utc=started_at_utc,
        completed_at_utc=_utcnow_iso(),
        request_id=result.request_id,
        http_status=200,
        usage=result.usage,
        content=result.content,
        finish_reason=result.finish_reason,
        client_latency_ms=result.client_latency_ms,
        time_to_first_token_ms=result.time_to_first_token_ms,
        generation_time_ms=result.generation_time_ms,
        output_tokens_per_second=result.output_tokens_per_second,
    )


@dataclasses.dataclass
class _RawResult:
    request_id: Optional[str]
    usage: UsageInfo
    content: Optional[str]
    finish_reason: Optional[str]
    client_latency_ms: float
    time_to_first_token_ms: Optional[float]
    generation_time_ms: Optional[float]
    output_tokens_per_second: Optional[float]


def _derive_timings(
    *, start: float, end: float, first_token_time: Optional[float], last_token_time: Optional[float], streaming: bool, output_tokens: Optional[int]
) -> tuple[float, Optional[float], Optional[float], Optional[float]]:
    client_latency_ms = (end - start) * 1000
    if not streaming:
        return client_latency_ms, None, None, (
            round(output_tokens / (client_latency_ms / 1000), 3) if output_tokens and client_latency_ms > 0 else None
        )
    ttft_ms = (first_token_time - start) * 1000 if first_token_time is not None else None
    generation_ms = (
        (last_token_time - first_token_time) * 1000 if first_token_time is not None and last_token_time is not None else None
    )
    tokens_per_second = (
        round(output_tokens / (generation_ms / 1000), 3) if output_tokens and generation_ms and generation_ms > 0 else None
    )
    return client_latency_ms, ttft_ms, generation_ms, tokens_per_second


def _execute_azure_openai(
    model_client: ModelClient,
    messages: list[dict],
    *,
    max_output_tokens: int,
    streaming: bool,
    temperature: float,
    top_p: float,
    seed: Optional[int],
    start: float,
) -> _RawResult:
    config = model_client.config
    kwargs: dict = {
        "model": config.deployment_name,
        "messages": messages,
        "max_completion_tokens": max_output_tokens,
        "stream": streaming,
    }
    if config.supports_temperature:
        kwargs["temperature"] = temperature
    if config.supports_top_p:
        kwargs["top_p"] = top_p
    if config.supports_seed and seed is not None:
        kwargs["seed"] = seed
    if streaming:
        kwargs["stream_options"] = {"include_usage": True}

    request_id: Optional[str] = None
    finish_reason: Optional[str] = None
    usage = UsageInfo()
    content_parts: list[str] = []
    first_token_time: Optional[float] = None
    last_token_time: Optional[float] = None

    if streaming:
        stream = model_client.client.chat.completions.create(**kwargs)
        for chunk in stream:
            now = time.monotonic()
            request_id = request_id or getattr(chunk, "id", None)
            choices = getattr(chunk, "choices", None) or []
            if choices:
                delta = choices[0].delta
                token_text = getattr(delta, "content", None)
                if token_text:
                    if first_token_time is None:
                        first_token_time = now
                    last_token_time = now
                    content_parts.append(token_text)
                fr = getattr(choices[0], "finish_reason", None)
                if fr:
                    finish_reason = fr
            chunk_usage = getattr(chunk, "usage", None)
            if chunk_usage is not None:
                usage = _normalize_openai_usage(chunk_usage)
        end = time.monotonic()
    else:
        response = model_client.client.chat.completions.create(**kwargs)
        end = time.monotonic()
        request_id = getattr(response, "id", None)
        choices = getattr(response, "choices", None) or []
        if choices:
            content_parts.append(choices[0].message.content or "")
            finish_reason = choices[0].finish_reason
        response_usage = getattr(response, "usage", None)
        if response_usage is not None:
            usage = _normalize_openai_usage(response_usage)

    client_latency_ms, ttft_ms, generation_ms, tokens_per_second = _derive_timings(
        start=start,
        end=end,
        first_token_time=first_token_time,
        last_token_time=last_token_time,
        streaming=streaming,
        output_tokens=usage.output_tokens,
    )
    return _RawResult(
        request_id=request_id,
        usage=usage,
        content="".join(content_parts) if content_parts else None,
        finish_reason=finish_reason,
        client_latency_ms=client_latency_ms,
        time_to_first_token_ms=ttft_ms,
        generation_time_ms=generation_ms,
        output_tokens_per_second=tokens_per_second,
    )


def _execute_azure_ai_inference(
    model_client: ModelClient,
    messages: list[dict],
    *,
    max_output_tokens: int,
    streaming: bool,
    temperature: float,
    top_p: float,
    seed: Optional[int],
    start: float,
) -> _RawResult:
    config = model_client.config
    kwargs: dict = {
        "model": config.deployment_name,
        "messages": messages,
        "max_tokens": max_output_tokens,
        "stream": streaming,
    }
    if config.supports_temperature:
        kwargs["temperature"] = temperature
    if config.supports_top_p:
        kwargs["top_p"] = top_p
    if config.supports_seed and seed is not None:
        kwargs["seed"] = seed

    request_id: Optional[str] = None
    finish_reason: Optional[str] = None
    usage = UsageInfo()
    content_parts: list[str] = []
    first_token_time: Optional[float] = None
    last_token_time: Optional[float] = None

    if streaming:
        stream = model_client.client.complete(**kwargs)
        for chunk in stream:
            now = time.monotonic()
            request_id = request_id or getattr(chunk, "id", None)
            choices = getattr(chunk, "choices", None) or []
            if choices:
                delta = choices[0].delta
                token_text = getattr(delta, "content", None)
                if token_text:
                    if first_token_time is None:
                        first_token_time = now
                    last_token_time = now
                    content_parts.append(token_text)
                fr = getattr(choices[0], "finish_reason", None)
                if fr:
                    finish_reason = fr
            chunk_usage = getattr(chunk, "usage", None)
            if chunk_usage is not None:
                usage = _normalize_inference_usage(chunk_usage)
        end = time.monotonic()
    else:
        response = model_client.client.complete(**kwargs)
        end = time.monotonic()
        request_id = getattr(response, "id", None)
        choices = getattr(response, "choices", None) or []
        if choices:
            content_parts.append(choices[0].message.content or "")
            finish_reason = choices[0].finish_reason
        response_usage = getattr(response, "usage", None)
        if response_usage is not None:
            usage = _normalize_inference_usage(response_usage)

    client_latency_ms, ttft_ms, generation_ms, tokens_per_second = _derive_timings(
        start=start,
        end=end,
        first_token_time=first_token_time,
        last_token_time=last_token_time,
        streaming=streaming,
        output_tokens=usage.output_tokens,
    )
    return _RawResult(
        request_id=request_id,
        usage=usage,
        content="".join(content_parts) if content_parts else None,
        finish_reason=finish_reason,
        client_latency_ms=client_latency_ms,
        time_to_first_token_ms=ttft_ms,
        generation_time_ms=generation_ms,
        output_tokens_per_second=tokens_per_second,
    )


def _normalize_openai_usage(usage_obj) -> UsageInfo:
    """`openai` 2.54.0's `CompletionUsage`: prompt_tokens, completion_tokens,
    total_tokens, plus optional prompt_tokens_details.cached_tokens and
    completion_tokens_details.reasoning_tokens.
    """
    cached_tokens = None
    prompt_details = getattr(usage_obj, "prompt_tokens_details", None)
    if prompt_details is not None:
        cached_tokens = getattr(prompt_details, "cached_tokens", None)
    reasoning_tokens = None
    completion_details = getattr(usage_obj, "completion_tokens_details", None)
    if completion_details is not None:
        reasoning_tokens = getattr(completion_details, "reasoning_tokens", None)
    return UsageInfo(
        input_tokens=getattr(usage_obj, "prompt_tokens", None),
        cached_input_tokens=cached_tokens,
        output_tokens=getattr(usage_obj, "completion_tokens", None),
        reasoning_tokens=reasoning_tokens,
        total_tokens=getattr(usage_obj, "total_tokens", None),
    )


def _normalize_inference_usage(usage_obj) -> UsageInfo:
    """`azure-ai-inference` 1.0.0b9's `CompletionsUsage`: prompt_tokens,
    completion_tokens, total_tokens only — no cached/reasoning
    breakdown. Left as None rather than assumed to be zero.
    """
    return UsageInfo(
        input_tokens=getattr(usage_obj, "prompt_tokens", None),
        cached_input_tokens=None,
        output_tokens=getattr(usage_obj, "completion_tokens", None),
        reasoning_tokens=None,
        total_tokens=getattr(usage_obj, "total_tokens", None),
    )


def _classify_exception(exc: Exception) -> tuple[Optional[int], str, str]:
    """Maps an SDK exception to (http_status, error_type, error_message)."""
    import openai
    from azure.core.exceptions import HttpResponseError, ServiceRequestError, ServiceResponseError

    if isinstance(exc, openai.APIStatusError):
        status = getattr(exc, "status_code", None)
        return status, _error_type_for_status(status), str(exc)
    if isinstance(exc, openai.APITimeoutError):
        return None, "timeout", str(exc)
    if isinstance(exc, openai.APIConnectionError):
        return None, "connection_error", str(exc)
    if isinstance(exc, HttpResponseError):
        status = getattr(exc, "status_code", None)
        return status, _error_type_for_status(status), str(exc)
    if isinstance(exc, (ServiceRequestError, ServiceResponseError)):
        return None, "connection_error", str(exc)
    return None, "unexpected_error", str(exc)


def _error_type_for_status(status: Optional[int]) -> str:
    if status == 429:
        return "throttled"
    if status == 408:
        return "timeout"
    if status is not None and 500 <= status < 600:
        return "server_error"
    if status is not None and 400 <= status < 500:
        return "client_error"
    return "unknown_error"
