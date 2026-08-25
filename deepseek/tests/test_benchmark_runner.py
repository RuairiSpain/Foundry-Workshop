"""Retry behavior, resume, duplicate detection, and redaction (spec
2.13). Uses fake SDK clients — no real network calls.
"""

from __future__ import annotations

import dataclasses
import random

import pytest

from src import benchmark_runner as br
from src.client_factory import ModelClient
from src.models import DeploymentResolutionError, PromptRecord, RequestRecord, redact_record
from tests.fakes import FakeCompletionResponse, FakeUsage, make_http_response_error


def _fake_client(config, backend="azure-ai-inference", *, responses=None, always_fail_status=None):
    """`responses` is an iterable of either FakeCompletionResponse or
    exceptions to raise, consumed in order, one per call to complete().
    """
    call_log = []

    class FakeSdk:
        def __init__(self):
            self._responses = iter(responses) if responses is not None else None

        def complete(self, **kwargs):
            call_log.append(kwargs)
            if always_fail_status is not None:
                raise make_http_response_error(always_fail_status, "fail")
            value = next(self._responses)
            if isinstance(value, Exception):
                raise value
            return value

    client = ModelClient(config=config, backend=backend, client=FakeSdk())
    return client, call_log


# --- retry behavior ------------------------------------------------------------


def test_execute_with_retries_succeeds_after_transient_failures(deepseek_config, default_settings):
    responses = [make_http_response_error(429, "throttled"), make_http_response_error(429, "throttled"), FakeCompletionResponse(content="ok", usage=FakeUsage(prompt_tokens=1, completion_tokens=1))]
    client, calls = _fake_client(deepseek_config, responses=responses)
    settings = dataclasses.replace(default_settings, max_retries=3)
    sleeps = []

    attempt, retry_count = br.execute_with_retries(
        client, [{"role": "user", "content": "hi"}], max_output_tokens=10, settings=settings, rng=random.Random(0), sleep_fn=sleeps.append
    )

    assert attempt.succeeded
    assert retry_count == 2
    assert len(calls) == 3
    assert len(sleeps) == 2  # slept before each retry, not after the final success


def test_execute_with_retries_stops_at_max_retries(deepseek_config, default_settings):
    client, calls = _fake_client(deepseek_config, always_fail_status=429)
    settings = dataclasses.replace(default_settings, max_retries=2)

    attempt, retry_count = br.execute_with_retries(
        client, [{"role": "user", "content": "hi"}], max_output_tokens=10, settings=settings, rng=random.Random(0), sleep_fn=lambda _: None
    )

    assert not attempt.succeeded
    assert retry_count == 2
    assert len(calls) == 3  # 1 initial attempt + 2 retries


def test_execute_with_retries_does_not_retry_a_non_retryable_failure(deepseek_config, default_settings):
    client, calls = _fake_client(deepseek_config, always_fail_status=400)
    settings = dataclasses.replace(default_settings, max_retries=5)

    attempt, retry_count = br.execute_with_retries(
        client, [{"role": "user", "content": "hi"}], max_output_tokens=10, settings=settings, rng=random.Random(0), sleep_fn=lambda _: None
    )

    assert not attempt.succeeded
    assert retry_count == 0
    assert len(calls) == 1  # no retries attempted for a 400


def test_backoff_seconds_grows_exponentially_and_is_capped():
    rng = random.Random(0)
    b1 = br.backoff_seconds(1, rng, base_seconds=1.0, max_seconds=100.0)
    b2 = br.backoff_seconds(2, rng, base_seconds=1.0, max_seconds=100.0)
    b3 = br.backoff_seconds(3, rng, base_seconds=1.0, max_seconds=100.0)
    # Roughly doubling (plus jitter), and never negative.
    assert 1.0 <= b1 <= 1.5
    assert 2.0 <= b2 <= 3.0
    assert 4.0 <= b3 <= 6.0
    capped = br.backoff_seconds(10, rng, base_seconds=1.0, max_seconds=5.0)
    assert capped <= 7.5  # capped base (5.0) + up to 50% jitter


# --- warm-up fail-fast -----------------------------------------------------------


def test_warm_up_raises_deployment_resolution_error_when_every_attempt_fails(deepseek_config, default_settings):
    client, _ = _fake_client(deepseek_config, always_fail_status=404)
    settings = dataclasses.replace(default_settings, warm_up_count=2)

    with pytest.raises(DeploymentResolutionError, match="deepseek-v4-flash-3107"):
        br.run_warm_up({deepseek_config.logical_name: client}, settings)


def test_warm_up_does_not_raise_when_some_attempts_succeed(deepseek_config, default_settings):
    responses = [make_http_response_error(500, "fail"), FakeCompletionResponse(content="ok", usage=None)]
    client, _ = _fake_client(deepseek_config, responses=responses)
    settings = dataclasses.replace(default_settings, warm_up_count=2)

    br.run_warm_up({deepseek_config.logical_name: client}, settings)  # does not raise


def test_warm_up_is_skipped_entirely_when_count_is_zero(deepseek_config, default_settings):
    client, calls = _fake_client(deepseek_config, always_fail_status=500)
    settings = dataclasses.replace(default_settings, warm_up_count=0)

    br.run_warm_up({deepseek_config.logical_name: client}, settings)  # does not raise, no calls made
    assert calls == []


# --- work item ordering ------------------------------------------------------------


def test_build_work_items_count_and_repeats(deepseek_config, azure_openai_config, sample_prompt):
    settings_obj = dataclasses.replace(_default(), repeats=3, randomize_model_order=False, randomize_prompt_order=False)
    items = br.build_work_items([deepseek_config, azure_openai_config], [sample_prompt], settings_obj)
    assert len(items) == 2 * 3  # 2 models * 3 repeats (1 prompt)
    assert [item.repeat for item in items if item.model_logical_name == deepseek_config.logical_name] == [1, 2, 3]


def test_build_work_items_ordering_is_reproducible_from_seed(deepseek_config, azure_openai_config):
    prompts = [
        PromptRecord(prompt_id=f"P{i}", category="c", difficulty="simple", max_output_tokens=10, prompt="x") for i in range(5)
    ]
    settings_a = dataclasses.replace(_default(), repeats=1, seed=123)
    settings_b = dataclasses.replace(_default(), repeats=1, seed=123)
    items_a = br.build_work_items([deepseek_config, azure_openai_config], prompts, settings_a)
    items_b = br.build_work_items([deepseek_config, azure_openai_config], prompts, settings_b)
    assert [i.key for i in items_a] == [i.key for i in items_b]


def _default():
    from src.models import BenchmarkSettings

    return BenchmarkSettings(run_id="r", warm_up_count=0, repeats=1, concurrency=1, streaming=False)


# --- resume / duplicate detection -------------------------------------------------


def _sample_record(**overrides) -> RequestRecord:
    base = dict(
        benchmark_run_id="run-1",
        prompt_id="P1",
        category="c",
        difficulty="simple",
        model="deepseek-v4-flash",
        deployment_name="deepseek-v4-flash-3107",
        provider="deepseek",
        region="eastus",
        repeat=1,
        streaming=False,
        started_at_utc="2026-01-01T00:00:00+00:00",
        completed_at_utc="2026-01-01T00:00:01+00:00",
    )
    base.update(overrides)
    return RequestRecord(**base)


def test_load_completed_keys_reads_back_written_records(tmp_path):
    path = tmp_path / "requests.jsonl"
    with br.JsonlWriter(path, resume=False) as writer:
        writer.write(_sample_record(prompt_id="P1", repeat=1))
        writer.write(_sample_record(prompt_id="P1", repeat=2))

    keys = br.load_completed_keys(path)
    assert keys == {("deepseek-v4-flash", "P1", 1), ("deepseek-v4-flash", "P1", 2)}


def test_load_completed_keys_filters_by_run_id(tmp_path):
    path = tmp_path / "requests.jsonl"
    with br.JsonlWriter(path, resume=False) as writer:
        writer.write(_sample_record(benchmark_run_id="run-A", prompt_id="P1", repeat=1))
        writer.write(_sample_record(benchmark_run_id="run-B", prompt_id="P1", repeat=1))

    keys_a = br.load_completed_keys(path, run_id="run-A")
    assert keys_a == {("deepseek-v4-flash", "P1", 1)}


def test_filter_for_resume_skips_already_completed_items(sample_prompt):
    items = [br.WorkItem("deepseek-v4-flash", sample_prompt, repeat) for repeat in (1, 2, 3)]
    completed = {("deepseek-v4-flash", sample_prompt.prompt_id, 1)}
    remaining = br.filter_for_resume(items, completed)
    assert [item.repeat for item in remaining] == [2, 3]


def test_jsonl_writer_resume_true_appends_to_existing_file(tmp_path):
    path = tmp_path / "requests.jsonl"
    with br.JsonlWriter(path, resume=False) as writer:
        writer.write(_sample_record(prompt_id="P1"))
    with br.JsonlWriter(path, resume=True) as writer:
        writer.write(_sample_record(prompt_id="P2"))

    records = br.load_records(path)
    assert {r.prompt_id for r in records} == {"P1", "P2"}


def test_jsonl_writer_resume_false_overwrites_existing_file(tmp_path):
    path = tmp_path / "requests.jsonl"
    with br.JsonlWriter(path, resume=False) as writer:
        writer.write(_sample_record(prompt_id="P1"))
    with br.JsonlWriter(path, resume=False) as writer:
        writer.write(_sample_record(prompt_id="P2"))

    records = br.load_records(path)
    assert {r.prompt_id for r in records} == {"P2"}


def test_end_to_end_run_produces_no_duplicate_keys_across_resume(tmp_path, deepseek_config, default_settings):
    prompts = [PromptRecord(prompt_id="P1", category="c", difficulty="simple", max_output_tokens=10, prompt="hi")]
    output_path = tmp_path / "requests.jsonl"

    # First run: one request succeeds.
    responses_1 = [FakeCompletionResponse(content="a", usage=FakeUsage(prompt_tokens=5, completion_tokens=2))]
    client_1, _ = _fake_client(deepseek_config, responses=responses_1)
    settings = dataclasses.replace(default_settings, repeats=1, warm_up_count=0)
    br.run(
        {deepseek_config.logical_name: client_1},
        [deepseek_config],
        prompts,
        settings,
        region="eastus",
        pricing_entries=[],
        output_path=output_path,
    )

    # "Resume": same run_id, same work items — should produce zero new records.
    client_2, calls_2 = _fake_client(deepseek_config, responses=[])
    new_records = br.run(
        {deepseek_config.logical_name: client_2},
        [deepseek_config],
        prompts,
        settings,
        region="eastus",
        pricing_entries=[],
        output_path=output_path,
        resume=True,
    )

    assert new_records == []
    assert calls_2 == []  # no network calls at all — everything was already done
    all_records = br.load_records(output_path, run_id=settings.run_id)
    assert len(all_records) == 1  # not duplicated


# --- redaction ---------------------------------------------------------------------


def test_redact_record_clears_response_text_but_keeps_hash():
    record = _sample_record(response_text="the actual generated text", response_sha256="abc123")
    redacted = redact_record(record, keep_response_text=False)
    assert redacted.response_text is None
    assert redacted.response_sha256 == "abc123"


def test_redact_record_keeps_text_when_requested():
    record = _sample_record(response_text="the actual generated text")
    kept = redact_record(record, keep_response_text=True)
    assert kept.response_text == "the actual generated text"


def test_build_record_respects_store_response_text_false(deepseek_config, default_settings):
    settings = dataclasses.replace(default_settings, store_response_text=False)
    from src.inference_client import AttemptResult
    from src.models import UsageInfo

    attempt = AttemptResult(
        started_at_utc="2026-01-01T00:00:00+00:00",
        completed_at_utc="2026-01-01T00:00:01+00:00",
        request_id="req-1",
        http_status=200,
        usage=UsageInfo(input_tokens=5, output_tokens=2),
        content="sensitive generated content",
        finish_reason="stop",
        client_latency_ms=10.0,
        time_to_first_token_ms=None,
        generation_time_ms=None,
        output_tokens_per_second=None,
    )
    item = br.WorkItem("deepseek-v4-flash", PromptRecord(prompt_id="P1", category="c", difficulty="s", max_output_tokens=10, prompt="x"), 1)
    record = br.build_record(
        ModelClient(config=deepseek_config, backend="azure-ai-inference", client=None),
        item,
        client_request_id="req-uuid",
        attempt=attempt,
        retry_count=0,
        settings=settings,
        region="eastus",
        pricing_entries=[],
        as_of=__import__("datetime").date(2026, 1, 1),
    )

    assert record.response_text is None
    # The hash is still computed from the real content, even though the
    # text itself isn't stored — this is what lets a reviewer verify
    # reproducibility without the content ever being written to disk.
    assert record.response_sha256 is not None
