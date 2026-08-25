"""Turns raw per-request records into summary rows and an SDK-vs-Azure-
Monitor reconciliation (spec 2.11, section 4).

Percentiles are always computed from the underlying request records
directly — never by averaging pre-computed percentiles across prompts,
which spec 2.11 explicitly calls out as wrong.
"""

from __future__ import annotations

import csv
import math
import statistics
from pathlib import Path
from typing import Optional

from .azure_monitor import MetricQueryResult
from .models import ModelSummaryRow, ReconciliationRow, RequestRecord

# Plausible, non-exhaustive explanations for an SDK/Azure Monitor gap
# (spec section 4). Recorded on a reconciliation row when the gap
# exceeds the threshold below — never used to force the two numbers to
# agree.
KNOWN_DISCREPANCY_REASONS = [
    "Warm-up traffic entered the Azure Monitor window.",
    "Retries produced additional physical inference requests.",
    "Other users called the same deployment.",
    "Azure Monitor aggregation boundaries did not align with the run.",
    "A provider exposed different usage fields.",
    "Cached tokens were represented differently.",
    "Metrics were unavailable or delayed.",
]

_NOTEWORTHY_DIFFERENCE_PCT = 1.0


def percentile(values: list[float], p: float) -> Optional[float]:
    """Linear-interpolation percentile (the same method numpy's default
    `numpy.percentile` uses), computed without a numpy dependency.
    """
    if not values:
        return None
    data = sorted(values)
    if len(data) == 1:
        return data[0]
    rank = (len(data) - 1) * (p / 100)
    lower = math.floor(rank)
    upper = math.ceil(rank)
    if lower == upper:
        return data[int(rank)]
    lower_value = data[int(lower)] * (upper - rank)
    upper_value = data[int(upper)] * (rank - lower)
    return lower_value + upper_value


def _summarize_group(model: str, category: str, group: list[RequestRecord]) -> ModelSummaryRow:
    attempted = len(group)
    succeeded = sum(1 for record in group if record.succeeded)
    failed = attempted - succeeded
    throttled = sum(1 for record in group if record.throttled)
    total_retries = sum(record.retry_count for record in group)
    retry_rate = total_retries / attempted if attempted else 0.0

    input_tokens = sum(record.input_tokens or 0 for record in group)
    output_tokens = sum(record.output_tokens or 0 for record in group)
    total_tokens = sum(record.total_tokens or 0 for record in group)

    latencies = [record.client_latency_ms for record in group if record.client_latency_ms is not None]
    ttft_values = [record.time_to_first_token_ms for record in group if record.time_to_first_token_ms is not None]
    tps_values = [record.output_tokens_per_second for record in group if record.output_tokens_per_second is not None]

    estimated_total_cost = sum(record.estimated_total_cost or 0.0 for record in group)
    cost_per_request = estimated_total_cost / attempted if attempted else 0.0

    return ModelSummaryRow(
        model=model,
        category=category,
        requests_attempted=attempted,
        requests_succeeded=succeeded,
        requests_failed=failed,
        throttled_requests=throttled,
        retry_rate=round(retry_rate, 4),
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        total_tokens=total_tokens,
        mean_latency_ms=round(statistics.mean(latencies), 3) if latencies else None,
        median_latency_ms=round(statistics.median(latencies), 3) if latencies else None,
        p50_latency_ms=_round_or_none(percentile(latencies, 50)),
        p90_latency_ms=_round_or_none(percentile(latencies, 90)),
        p95_latency_ms=_round_or_none(percentile(latencies, 95)),
        p99_latency_ms=_round_or_none(percentile(latencies, 99)),
        median_ttft_ms=round(statistics.median(ttft_values), 3) if ttft_values else None,
        p95_ttft_ms=_round_or_none(percentile(ttft_values, 95)),
        median_output_tokens_per_second=round(statistics.median(tps_values), 3) if tps_values else None,
        estimated_total_cost=round(estimated_total_cost, 6),
        estimated_cost_per_request=round(cost_per_request, 6),
        estimated_cost_per_1000_requests=round(cost_per_request * 1000, 6),
    )


def _round_or_none(value: Optional[float]) -> Optional[float]:
    return round(value, 3) if value is not None else None


def summarize(records: list[RequestRecord], *, include_overall: bool = True) -> list[ModelSummaryRow]:
    """One row per (model, category), plus one "__all__" category row
    per model when `include_overall` is True — useful for an at-a-glance
    comparison, always alongside the per-category breakdown, never
    instead of it.
    """
    by_model_category: dict[tuple[str, str], list[RequestRecord]] = {}
    by_model: dict[str, list[RequestRecord]] = {}
    for record in records:
        by_model_category.setdefault((record.model, record.category), []).append(record)
        by_model.setdefault(record.model, []).append(record)

    rows = [_summarize_group(model, category, group) for (model, category), group in sorted(by_model_category.items())]
    if include_overall:
        rows.extend(_summarize_group(model, "__all__", group) for model, group in sorted(by_model.items()))
    return rows


def reconcile_tokens(
    *,
    model: str,
    deployment_name: str,
    sdk_input_tokens: int,
    sdk_output_tokens: int,
    azure_monitor_results: dict[str, MetricQueryResult],
) -> list[ReconciliationRow]:
    """Compares SDK-summed token totals against Azure Monitor's
    "Processed Prompt Tokens" / "Generated Completion Tokens" metrics
    for one model (spec section 4). A metric Azure Monitor couldn't
    return is recorded as unavailable, never treated as zero.
    """
    mapping = [
        ("input_tokens", "Processed Prompt Tokens", sdk_input_tokens),
        ("output_tokens", "Generated Completion Tokens", sdk_output_tokens),
    ]
    rows: list[ReconciliationRow] = []
    for metric_key, azure_monitor_metric_name, sdk_value in mapping:
        result = azure_monitor_results.get(azure_monitor_metric_name)
        if result is None or not result.available:
            error = result.error if result is not None else "not queried"
            rows.append(
                ReconciliationRow(
                    model=model,
                    deployment_name=deployment_name,
                    metric=metric_key,
                    sdk_value=sdk_value,
                    azure_monitor_value=None,
                    difference=None,
                    difference_pct=None,
                    notes=f"Azure Monitor metric unavailable ({error}).",
                )
            )
            continue

        am_value = result.sum_total()
        if am_value is None:
            rows.append(
                ReconciliationRow(
                    model=model,
                    deployment_name=deployment_name,
                    metric=metric_key,
                    sdk_value=sdk_value,
                    azure_monitor_value=None,
                    difference=None,
                    difference_pct=None,
                    notes="Azure Monitor returned no data points for this window.",
                )
            )
            continue

        difference = sdk_value - am_value
        difference_pct = (difference / am_value * 100) if am_value else None
        notes = ""
        if difference_pct is not None and abs(difference_pct) > _NOTEWORTHY_DIFFERENCE_PCT:
            notes = "Possible causes: " + "; ".join(KNOWN_DISCREPANCY_REASONS)
        rows.append(
            ReconciliationRow(
                model=model,
                deployment_name=deployment_name,
                metric=metric_key,
                sdk_value=round(sdk_value, 3),
                azure_monitor_value=round(am_value, 3),
                difference=round(difference, 3),
                difference_pct=round(difference_pct, 4) if difference_pct is not None else None,
                notes=notes,
            )
        )
    return rows


# ---------------------------------------------------------------------------
# Output writers
# ---------------------------------------------------------------------------


def write_model_summary_csv(rows: list[ModelSummaryRow], path: Path) -> None:
    _write_csv(rows, path)


def write_reconciliation_csv(rows: list[ReconciliationRow], path: Path) -> None:
    _write_csv(rows, path)


def write_results_csv(records: list[RequestRecord], path: Path) -> None:
    _write_csv(records, path)


def _write_csv(rows: list, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames = list(rows[0].to_dict().keys())
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row.to_dict())
