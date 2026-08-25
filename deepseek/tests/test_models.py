"""Small dataclass helper behaviors not already exercised elsewhere."""

from __future__ import annotations

from src.models import RequestRecord, UsageInfo, hash_text


def test_usage_info_derives_total_when_missing():
    usage = UsageInfo(input_tokens=10, output_tokens=5)
    assert usage.total_tokens == 15


def test_usage_info_leaves_total_none_when_inputs_missing():
    usage = UsageInfo(input_tokens=None, output_tokens=5)
    assert usage.total_tokens is None


def test_usage_info_respects_explicit_total():
    usage = UsageInfo(input_tokens=10, output_tokens=5, total_tokens=999)
    assert usage.total_tokens == 999


def test_hash_text_is_deterministic():
    assert hash_text("hello") == hash_text("hello")


def test_hash_text_of_none_is_none():
    assert hash_text(None) is None


def test_hash_text_differs_for_different_content():
    assert hash_text("hello") != hash_text("world")


def test_request_record_succeeded_requires_2xx_and_no_error():
    ok = RequestRecord(
        benchmark_run_id="r", prompt_id="p", category="c", difficulty="s", model="m", deployment_name="d",
        provider="deepseek", region="eastus", repeat=1, streaming=False,
        started_at_utc="t", completed_at_utc="t", http_status=200,
    )
    assert ok.succeeded

    failed = RequestRecord(
        benchmark_run_id="r", prompt_id="p", category="c", difficulty="s", model="m", deployment_name="d",
        provider="deepseek", region="eastus", repeat=1, streaming=False,
        started_at_utc="t", completed_at_utc="t", http_status=500, error_type="server_error",
    )
    assert not failed.succeeded


def test_request_record_throttled_is_only_429():
    throttled = RequestRecord(
        benchmark_run_id="r", prompt_id="p", category="c", difficulty="s", model="m", deployment_name="d",
        provider="deepseek", region="eastus", repeat=1, streaming=False,
        started_at_utc="t", completed_at_utc="t", http_status=429,
    )
    assert throttled.throttled
    not_throttled = RequestRecord(
        benchmark_run_id="r", prompt_id="p", category="c", difficulty="s", model="m", deployment_name="d",
        provider="deepseek", region="eastus", repeat=1, streaming=False,
        started_at_utc="t", completed_at_utc="t", http_status=500,
    )
    assert not not_throttled.throttled


def test_request_record_to_json_line_round_trips():
    import json

    record = RequestRecord(
        benchmark_run_id="r", prompt_id="p", category="c", difficulty="s", model="m", deployment_name="d",
        provider="deepseek", region="eastus", repeat=1, streaming=False,
        started_at_utc="t", completed_at_utc="t", http_status=200,
    )
    line = record.to_json_line()
    data = json.loads(line)
    assert data["prompt_id"] == "p"
    assert RequestRecord(**data) == record
