"""Percentile aggregation and SDK-vs-Azure-Monitor reconciliation
(spec 2.11, section 4, spec 2.13).
"""

from __future__ import annotations

import dataclasses

import pytest

from src.aggregation import percentile, reconcile_tokens, summarize, write_model_summary_csv, write_reconciliation_csv, write_results_csv
from src.azure_monitor import MetricPoint, MetricQueryResult
from src.models import RequestRecord


def _record(**overrides) -> RequestRecord:
    base = dict(
        benchmark_run_id="run-1",
        prompt_id="P1",
        category="classification",
        difficulty="simple",
        model="deepseek-v4-flash",
        deployment_name="deepseek-v4-flash-3107",
        provider="deepseek",
        region="eastus",
        repeat=1,
        streaming=False,
        started_at_utc="2026-01-01T00:00:00+00:00",
        completed_at_utc="2026-01-01T00:00:01+00:00",
        http_status=200,
        retry_count=0,
        input_tokens=100,
        output_tokens=50,
        total_tokens=150,
        client_latency_ms=100.0,
        time_to_first_token_ms=None,
        generation_time_ms=None,
        output_tokens_per_second=50.0,
        estimated_total_cost=0.001,
    )
    base.update(overrides)
    return RequestRecord(**base)


# --- percentile ---------------------------------------------------------------


def test_percentile_of_empty_list_is_none():
    assert percentile([], 50) is None


def test_percentile_of_single_value():
    assert percentile([42.0], 90) == 42.0


def test_percentile_p50_matches_median_for_odd_length():
    assert percentile([1, 2, 3, 4, 5], 50) == 3


def test_percentile_p100_is_the_maximum():
    assert percentile([1, 2, 3, 100], 100) == 100


def test_percentile_p0_is_the_minimum():
    assert percentile([1, 2, 3, 100], 0) == 1


def test_percentile_is_computed_from_raw_values_not_averaged():
    """The specific case spec 2.11 calls out: percentiles must come from
    the underlying records, not from averaging per-prompt percentiles.
    A skewed distribution's P95 must reflect the outlier, which an
    average-of-percentiles approach would smooth away.
    """
    latencies = [100.0] * 19 + [10_000.0]  # one big outlier among 20 requests
    p95 = percentile(latencies, 95)
    # Linear interpolation between the 19th (100) and 20th (10,000)
    # sorted values pulls P95 well above every non-outlier value — the
    # outlier is visible. Averaging 20 identical per-record "P95"s
    # (each just that record's own latency) would instead average out
    # to roughly the mean, hiding it.
    assert p95 > 500


# --- summarize ------------------------------------------------------------------


def test_summarize_groups_by_model_and_category():
    records = [
        _record(model="a", category="cat1"),
        _record(model="a", category="cat1"),
        _record(model="a", category="cat2"),
        _record(model="b", category="cat1"),
    ]
    rows = summarize(records, include_overall=False)
    keys = {(row.model, row.category) for row in rows}
    assert keys == {("a", "cat1"), ("a", "cat2"), ("b", "cat1")}


def test_summarize_counts_succeeded_failed_and_throttled():
    records = [
        _record(http_status=200),
        _record(http_status=500, error_type="server_error"),
        _record(http_status=429, error_type="throttled"),
    ]
    rows = summarize(records, include_overall=False)
    row = rows[0]
    assert row.requests_attempted == 3
    assert row.requests_succeeded == 1
    assert row.requests_failed == 2
    assert row.throttled_requests == 1


def test_summarize_retry_rate_is_average_retries_per_request():
    records = [_record(retry_count=0), _record(retry_count=2), _record(retry_count=4)]
    rows = summarize(records, include_overall=False)
    assert rows[0].retry_rate == pytest.approx(2.0)


def test_summarize_sums_tokens_and_cost():
    records = [_record(input_tokens=100, output_tokens=50, total_tokens=150, estimated_total_cost=0.01), _record(input_tokens=200, output_tokens=60, total_tokens=260, estimated_total_cost=0.02)]
    rows = summarize(records, include_overall=False)
    row = rows[0]
    assert row.input_tokens == 300
    assert row.output_tokens == 110
    assert row.total_tokens == 410
    assert row.estimated_total_cost == pytest.approx(0.03)
    assert row.estimated_cost_per_request == pytest.approx(0.015)
    assert row.estimated_cost_per_1000_requests == pytest.approx(15.0)


def test_summarize_percentiles_ignore_missing_latency_values():
    records = [_record(client_latency_ms=100.0), _record(client_latency_ms=None, http_status=500, error_type="server_error")]
    rows = summarize(records, include_overall=False)
    assert rows[0].mean_latency_ms == pytest.approx(100.0)


def test_summarize_includes_overall_row_per_model_by_default():
    records = [_record(model="a", category="cat1"), _record(model="a", category="cat2")]
    rows = summarize(records)
    categories = {row.category for row in rows if row.model == "a"}
    assert categories == {"cat1", "cat2", "__all__"}


def test_summarize_empty_records_returns_no_rows():
    assert summarize([]) == []


# --- reconciliation --------------------------------------------------------------


def test_reconcile_tokens_reports_a_small_difference_without_flagging_it():
    """The exact example from spec section 4: a 0.21% gap is small
    enough to report plainly, without the "possible causes" callout —
    that callout is reserved for a gap worth investigating.
    """
    am_results = {
        "Processed Prompt Tokens": MetricQueryResult(
            metric_name="Processed Prompt Tokens", unit="Count", available=True, points=[MetricPoint(timestamp=None, average=None, total=126_100, count=None, minimum=None, maximum=None)]
        ),
        "Generated Completion Tokens": MetricQueryResult(
            metric_name="Generated Completion Tokens", unit="Count", available=True, points=[MetricPoint(timestamp=None, average=None, total=25_000, count=None, minimum=None, maximum=None)]
        ),
    }
    rows = reconcile_tokens(model="gpt-5-sol", deployment_name="gpt-5-sol", sdk_input_tokens=125_840, sdk_output_tokens=25_000, azure_monitor_results=am_results)

    input_row = next(r for r in rows if r.metric == "input_tokens")
    assert input_row.sdk_value == 125_840
    assert input_row.azure_monitor_value == 126_100
    assert input_row.difference == pytest.approx(-260)
    assert input_row.difference_pct == pytest.approx(-260 / 126_100 * 100, rel=1e-3)
    assert input_row.notes == ""  # under the noteworthy-difference threshold

    output_row = next(r for r in rows if r.metric == "output_tokens")
    assert output_row.difference == pytest.approx(0)
    assert output_row.notes == ""


def test_reconcile_tokens_flags_a_large_difference_with_possible_causes():
    am_results = {
        "Processed Prompt Tokens": MetricQueryResult(
            metric_name="Processed Prompt Tokens", unit="Count", available=True, points=[MetricPoint(timestamp=None, average=None, total=100_000, count=None, minimum=None, maximum=None)]
        ),
        "Generated Completion Tokens": MetricQueryResult(
            metric_name="Generated Completion Tokens", unit="Count", available=True, points=[MetricPoint(timestamp=None, average=None, total=20_000, count=None, minimum=None, maximum=None)]
        ),
    }
    # 10% higher than Azure Monitor's total — well past the 1% threshold.
    rows = reconcile_tokens(model="gpt-5-sol", deployment_name="gpt-5-sol", sdk_input_tokens=110_000, sdk_output_tokens=20_000, azure_monitor_results=am_results)

    input_row = next(r for r in rows if r.metric == "input_tokens")
    assert "Possible causes" in input_row.notes
    assert "Retries produced additional physical inference requests." in input_row.notes


def test_reconcile_tokens_marks_missing_metric_as_unavailable_not_zero():
    """Spec 2.9: the client must tolerate missing metrics and mark them
    unavailable rather than treating the query as failed — and never
    silently compare the SDK value against a fabricated zero.
    """
    unavailable = MetricQueryResult(metric_name="Processed Prompt Tokens", unit=None, available=False, error="metric not supported for this deployment")
    rows = reconcile_tokens(
        model="deepseek-v4-flash",
        deployment_name="deepseek-v4-flash-3107",
        sdk_input_tokens=1000,
        sdk_output_tokens=200,
        azure_monitor_results={"Processed Prompt Tokens": unavailable},
    )
    input_row = next(r for r in rows if r.metric == "input_tokens")
    assert input_row.azure_monitor_value is None
    assert input_row.difference is None
    assert "unavailable" in input_row.notes

    output_row = next(r for r in rows if r.metric == "output_tokens")
    assert output_row.azure_monitor_value is None
    assert "not queried" in output_row.notes


def test_reconcile_tokens_handles_metric_present_but_no_data_points():
    empty = MetricQueryResult(metric_name="Processed Prompt Tokens", unit="Count", available=True, points=[])
    rows = reconcile_tokens(model="m", deployment_name="d", sdk_input_tokens=10, sdk_output_tokens=5, azure_monitor_results={"Processed Prompt Tokens": empty})
    input_row = next(r for r in rows if r.metric == "input_tokens")
    assert input_row.azure_monitor_value is None
    assert "no data points" in input_row.notes


# --- CSV writers -----------------------------------------------------------------


def test_write_model_summary_csv(tmp_path):
    rows = summarize([_record()], include_overall=False)
    path = tmp_path / "model_summary.csv"
    write_model_summary_csv(rows, path)
    content = path.read_text(encoding="utf-8")
    assert "model" in content.splitlines()[0]
    assert "deepseek-v4-flash" in content


def test_write_results_csv(tmp_path):
    path = tmp_path / "results.csv"
    write_results_csv([_record()], path)
    content = path.read_text(encoding="utf-8")
    assert "prompt_id" in content.splitlines()[0]
    assert "P1" in content


def test_write_reconciliation_csv(tmp_path):
    rows = reconcile_tokens(
        model="m",
        deployment_name="d",
        sdk_input_tokens=10,
        sdk_output_tokens=5,
        azure_monitor_results={},
    )
    path = tmp_path / "reconciliation.csv"
    write_reconciliation_csv(rows, path)
    content = path.read_text(encoding="utf-8")
    assert "metric" in content.splitlines()[0]


def test_write_csv_handles_empty_rows(tmp_path):
    path = tmp_path / "empty.csv"
    write_results_csv([], path)
    assert path.read_text(encoding="utf-8") == ""
