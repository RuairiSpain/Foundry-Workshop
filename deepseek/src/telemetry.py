"""OpenTelemetry instrumentation, exported to Application Insights.

One parent span per invocation, `benchmark.model_request`, with the
attributes spec 2.10 recommends. The complete prompt/response text is
never attached to a span — only IDs and a SHA-256 hash — so Application
Insights never becomes a second, less-controlled place prompt content
ends up (`RequestRecord.response_text` storage is a separate, explicit
opt-in; see `models.redact_record()`).

Verified against installed packages: `azure-monitor-opentelemetry`
1.8.9's `configure_azure_monitor(connection_string=...)`,
`opentelemetry-api` 1.43.0's `trace.get_tracer()` /
`Status`/`StatusCode`.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator, Optional

from .models import RequestRecord

_TRACER_NAME = "deepseek-benchmark"
_configured = False


def init_telemetry(connection_string: Optional[str]) -> bool:
    """Configures the Application Insights exporter once per process.

    A no-op (returns False) when `connection_string` is falsy —
    spans are still created against the default OpenTelemetry no-op
    tracer provider in that case, so instrumented code never needs an
    `if telemetry_enabled` branch of its own.
    """
    global _configured
    if not connection_string:
        return False
    if _configured:
        return True
    from azure.monitor.opentelemetry import configure_azure_monitor

    configure_azure_monitor(connection_string=connection_string)
    _configured = True
    return True


def get_tracer():
    from opentelemetry import trace

    return trace.get_tracer(_TRACER_NAME)


def build_span_attributes(
    record: RequestRecord,
    *,
    response_model: Optional[str] = None,
    server_address: Optional[str] = None,
) -> dict:
    """Maps a RequestRecord onto the attribute names spec 2.10
    recommends. Values that are None are omitted (span attributes
    don't accept None) rather than coerced to a string.
    """
    attributes = {
        "benchmark.run_id": record.benchmark_run_id,
        "benchmark.prompt_id": record.prompt_id,
        "benchmark.repeat": record.repeat,
        "gen_ai.system": record.provider,
        "gen_ai.request.model": record.deployment_name,
        "gen_ai.response.model": response_model,
        "azure.deployment.name": record.deployment_name,
        "server.address": server_address,
        "service.request_id": record.request_id,
        "client.request_id": record.client_request_id,
        "gen_ai.usage.input_tokens": record.input_tokens,
        "gen_ai.usage.output_tokens": record.output_tokens,
        "benchmark.cached_input_tokens": record.cached_input_tokens,
        "benchmark.reasoning_tokens": record.reasoning_tokens,
        "benchmark.client_latency_ms": record.client_latency_ms,
        "benchmark.ttft_ms": record.time_to_first_token_ms,
        "benchmark.generation_time_ms": record.generation_time_ms,
        "benchmark.retry_count": record.retry_count,
        "benchmark.success": record.succeeded,
        # Beyond the recommended set: a content hash costs nothing and
        # lets a reviewer confirm two runs produced identical output
        # without ever attaching the text itself.
        "benchmark.response_sha256": record.response_sha256,
    }
    return {key: value for key, value in attributes.items() if value is not None}


@contextmanager
def model_request_span(tracer, attributes: dict) -> Iterator[object]:
    """Opens `benchmark.model_request`, sets the given attributes, and
    marks the span's status from `benchmark.success` on exit.
    """
    from opentelemetry.trace import Status, StatusCode

    with tracer.start_as_current_span("benchmark.model_request") as span:
        for key, value in attributes.items():
            span.set_attribute(key, value)
        try:
            yield span
        finally:
            if attributes.get("benchmark.success") is False:
                span.set_status(Status(StatusCode.ERROR))
