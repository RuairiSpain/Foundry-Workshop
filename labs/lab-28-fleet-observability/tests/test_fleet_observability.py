"""Tests for solution/fleet_observability.py.

main() is excluded from coverage — real SDK/CLI entry point, exercised
manually, not under test.
"""

import pytest

from solution.fleet_observability import (
    FLEET_TRACES,
    correlate_metric_to_trace,
    find_expensive_traces,
    find_failed_traces,
    find_slow_traces,
    summarize_by_agent,
)


def test_find_slow_traces_finds_the_planted_latency_regression():
    slow = find_slow_traces(FLEET_TRACES, threshold_ms=2000)

    assert [trace["trace_id"] for trace in slow] == ["tr-007"]


def test_find_slow_traces_sorts_slowest_first():
    slow = find_slow_traces(FLEET_TRACES, threshold_ms=400)

    durations = [trace["duration_ms"] for trace in slow]
    assert durations == sorted(durations, reverse=True)


def test_find_expensive_traces_finds_the_planted_cost_spike():
    expensive = find_expensive_traces(FLEET_TRACES, threshold_usd=0.1)

    assert [trace["trace_id"] for trace in expensive] == ["tr-005"]


def test_find_failed_traces_finds_the_planted_failure():
    failed = find_failed_traces(FLEET_TRACES)

    assert [trace["trace_id"] for trace in failed] == ["tr-004"]


def test_summarize_by_agent_aggregates_correctly_for_the_concierge():
    summary = summarize_by_agent(FLEET_TRACES)

    concierge_stats = summary["cascadia-concierge"]
    assert concierge_stats.trace_count == 2
    assert concierge_stats.total_cost_usd == pytest.approx(0.321)
    assert concierge_stats.failure_rate == 0.0


def test_summarize_by_agent_computes_a_nonzero_failure_rate_for_order_status():
    summary = summarize_by_agent(FLEET_TRACES)

    order_stats = summary["cascadia-order-status"]
    assert order_stats.trace_count == 2
    assert order_stats.failure_rate == 0.5


def test_correlate_metric_to_trace_finds_the_matching_record():
    trace = correlate_metric_to_trace(FLEET_TRACES, trace_id="tr-005")

    assert trace["agent_name"] == "cascadia-concierge"
    assert trace["cost_usd"] == 0.312


def test_correlate_metric_to_trace_raises_for_an_unknown_id():
    with pytest.raises(KeyError, match="tr-999"):
        correlate_metric_to_trace(FLEET_TRACES, trace_id="tr-999")
