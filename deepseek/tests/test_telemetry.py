"""Telemetry span attributes never carry raw prompt/response text
(spec 2.10, spec 2.13's "redaction of sensitive telemetry fields").
"""

from __future__ import annotations

from src.models import RequestRecord
from src.telemetry import build_span_attributes


def _record(**overrides) -> RequestRecord:
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
        streaming=True,
        started_at_utc="2026-01-01T00:00:00+00:00",
        completed_at_utc="2026-01-01T00:00:01+00:00",
        client_request_id="req-uuid",
        http_status=200,
        input_tokens=10,
        output_tokens=5,
        client_latency_ms=100.0,
        response_text="the full generated response text",
        response_sha256="abc123",
    )
    base.update(overrides)
    return RequestRecord(**base)


def test_span_attributes_never_include_response_text():
    record = _record()
    attributes = build_span_attributes(record)
    assert "response_text" not in attributes
    for value in attributes.values():
        assert value != record.response_text  # the raw text never leaks into any attribute value


def test_span_attributes_include_prompt_id_and_hash_not_content():
    record = _record()
    attributes = build_span_attributes(record)
    assert attributes["benchmark.prompt_id"] == "P1"
    assert attributes["benchmark.response_sha256"] == "abc123"


def test_span_attributes_omit_none_values():
    record = _record(request_id=None, reasoning_tokens=None)
    attributes = build_span_attributes(record)
    assert "service.request_id" not in attributes
    assert "benchmark.reasoning_tokens" not in attributes


def test_span_attributes_map_success_flag():
    succeeded = _record(http_status=200, error_type=None)
    failed = _record(http_status=500, error_type="server_error")
    assert build_span_attributes(succeeded)["benchmark.success"] is True
    assert build_span_attributes(failed)["benchmark.success"] is False


def test_span_attributes_include_gen_ai_usage_fields():
    record = _record(input_tokens=42, output_tokens=7)
    attributes = build_span_attributes(record)
    assert attributes["gen_ai.usage.input_tokens"] == 42
    assert attributes["gen_ai.usage.output_tokens"] == 7
    assert attributes["gen_ai.system"] == "deepseek"
