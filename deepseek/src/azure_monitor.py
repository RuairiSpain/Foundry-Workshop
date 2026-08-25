"""Queries Azure Monitor for platform-level, deployment-aggregated
metrics — the independent validation source for the SDK-reported token
totals and latency (spec 1 and 2.9).

Verified against the actually-installed packages before writing this
module, and this turned up a real, worth-recording finding:
`azure-monitor-query` 2.0.0 (today's real latest on PyPI) no longer
ships `MetricsQueryClient` at all — only `LogsQueryClient` remains in
that package. Microsoft split metrics querying out into a new,
separate package, `azure-monitor-querymetrics` 1.0.0
(`MetricsClient.query_resources()`), which requires a *regional*
metrics endpoint (`https://<region>.metrics.monitor.azure.com`) rather
than a plain resource ID. To avoid that extra region-discovery step,
and because spec 2.9 explicitly allows "Azure Resource Manager or
Azure Monitor Query SDKs", this module uses `azure-mgmt-monitor`
7.0.0's `MonitorManagementClient` instead: `client.metrics.list()` for
the query itself and `client.metric_definitions.list()` for enumerating
what a resource actually exposes — one package, one client, no region
lookup, and it's the same ARM metrics REST API the retired
`MetricsQueryClient` used to wrap.

IMPORTANT: the exact Azure OpenAI metric names in
`AZURE_OPENAI_METRIC_NAMES` below are Microsoft's documented names, not
independently reproduced against a live resource (this sandbox has no
real Foundry resource to query). Confirm them against your own
resource's Metrics blade in the Foundry Portal before trusting the
reconciliation output. DeepSeek (and any other non-Azure-OpenAI
provider) gets no such hardcoded list at all, per spec 2.9 — its
metric names are only ever discovered by calling
`list_available_metric_names()` first.
"""

from __future__ import annotations

import dataclasses
import datetime as dt
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Microsoft's documented Azure OpenAI-specific metrics — prefer these
# over the generic "Latency" (Cognitive Services) metric, which
# Microsoft says can be misleading for Azure OpenAI workloads.
AZURE_OPENAI_METRIC_NAMES: dict[str, str] = {
    "AzureOpenAITimeToResponse": "Time to response",
    "AzureOpenAITTLTInMS": "Time to last token, in milliseconds",
    "AzureOpenAINormalizedTTFTInMS": "Normalized time to first token, in milliseconds",
    "AzureOpenAINormalizedTBTInMS": "Normalized time between tokens, in milliseconds",
    "Processed Prompt Tokens": "Prompt (input) tokens processed",
    "Generated Completion Tokens": "Completion (output) tokens generated",
}


@dataclasses.dataclass
class MetricPoint:
    timestamp: dt.datetime
    average: Optional[float]
    total: Optional[float]
    count: Optional[float]
    minimum: Optional[float]
    maximum: Optional[float]


@dataclasses.dataclass
class MetricQueryResult:
    """One metric's result. `available=False` means the metric could not
    be queried for this resource (unsupported for this deployment type,
    wrong name, or a transient query failure) — the caller marks it
    "unavailable" in aggregation output instead of treating the whole
    reconciliation as failed (spec 2.9's explicit tolerance requirement).
    """

    metric_name: str
    unit: Optional[str]
    available: bool
    points: list[MetricPoint] = dataclasses.field(default_factory=list)
    error: Optional[str] = None

    def sum_total(self) -> Optional[float]:
        """Sums the `total` aggregation across every point — the right
        reduction for a count-like metric (tokens, requests).
        """
        if not self.available or not self.points:
            return None
        values = [point.total for point in self.points if point.total is not None]
        return sum(values) if values else None

    def average_of_averages(self) -> Optional[float]:
        """Mean of the per-minute `average` values — a reasonable
        summary for a latency-like metric across a run window. Real
        percentiles for latency come from the SDK-side RequestRecords
        (aggregation.py), not from this coarser, pre-aggregated series —
        Azure Monitor's own per-minute averages can't be un-averaged
        back into a percentile.
        """
        if not self.available or not self.points:
            return None
        values = [point.average for point in self.points if point.average is not None]
        return sum(values) / len(values) if values else None


def build_resource_id(*, subscription_id: str, resource_group: str, foundry_resource_name: str) -> str:
    return (
        f"/subscriptions/{subscription_id}/resourceGroups/{resource_group}"
        f"/providers/Microsoft.CognitiveServices/accounts/{foundry_resource_name}"
    )


def build_monitor_client(token_credential, subscription_id: str):
    """Builds the ARM management client used for both metric enumeration
    and querying. Requires `AZURE_SUBSCRIPTION_ID` via the caller
    (`client_factory.EnvironmentSettings.require_azure_monitor_config()`
    should be called before this).
    """
    from azure.mgmt.monitor import MonitorManagementClient

    return MonitorManagementClient(credential=token_credential, subscription_id=subscription_id)


def list_available_metric_names(monitor_client, resource_id: str) -> set[str]:
    """Enumerates every metric name (and, implicitly, dimension) the
    resource actually exposes. Tolerant: returns an empty set and logs
    a warning on failure rather than raising — callers use this to
    decide *which* metrics are worth querying, so a failure here should
    degrade to "query nothing extra", not abort the run.
    """
    try:
        definitions = monitor_client.metric_definitions.list(resource_id)
        return {definition.name.value for definition in definitions if definition.name and definition.name.value}
    except Exception as exc:  # noqa: BLE001 - deliberately tolerant, see docstring
        logger.warning("Could not enumerate metric definitions for %s: %s", resource_id, exc)
        return set()


def query_metric(
    monitor_client,
    resource_id: str,
    metric_name: str,
    *,
    start: dt.datetime,
    end: dt.datetime,
    interval: dt.timedelta = dt.timedelta(minutes=1),
    deployment_dimension_filter: Optional[str] = None,
) -> MetricQueryResult:
    """Queries one metric over [start, end). Every metric is queried
    independently (not batched) so one unsupported or misspelled name
    can't fail the whole reconciliation — the ARM metrics API rejects
    an entire batched request if any one metric name in it is invalid
    for the resource.
    """
    timespan = f"{start.isoformat()}/{end.isoformat()}"
    interval_iso = _timedelta_to_iso8601(interval)
    try:
        response = monitor_client.metrics.list(
            resource_uri=resource_id,
            timespan=timespan,
            interval=interval_iso,
            metricnames=metric_name,
            aggregation="Average,Total,Count,Minimum,Maximum",
            filter=deployment_dimension_filter,
        )
    except Exception as exc:  # noqa: BLE001 - tolerated per spec 2.9
        logger.warning("Metric %r unavailable for %s: %s", metric_name, resource_id, exc)
        return MetricQueryResult(metric_name=metric_name, unit=None, available=False, error=str(exc))

    metrics = list(getattr(response, "value", None) or [])
    if not metrics:
        return MetricQueryResult(metric_name=metric_name, unit=None, available=False, error="No data returned")

    metric = metrics[0]
    unit = str(metric.unit) if getattr(metric, "unit", None) is not None else None
    points: list[MetricPoint] = []
    for series in getattr(metric, "timeseries", None) or []:
        for value in getattr(series, "data", None) or []:
            points.append(
                MetricPoint(
                    timestamp=value.time_stamp,
                    average=value.average,
                    total=value.total,
                    count=value.count,
                    minimum=value.minimum,
                    maximum=value.maximum,
                )
            )
    return MetricQueryResult(metric_name=metric_name, unit=unit, available=True, points=points)


def query_metrics_for_window(
    monitor_client,
    resource_id: str,
    metric_names: list[str],
    *,
    start: dt.datetime,
    end: dt.datetime,
    interval: dt.timedelta = dt.timedelta(minutes=1),
    deployment_dimension_filter: Optional[str] = None,
) -> dict[str, MetricQueryResult]:
    """Queries every name in `metric_names` and returns a dict keyed by
    metric name, one entry per name regardless of whether it succeeded
    — a missing/failed metric is present with `available=False`, never
    silently dropped from the result.
    """
    return {
        name: query_metric(
            monitor_client,
            resource_id,
            name,
            start=start,
            end=end,
            interval=interval,
            deployment_dimension_filter=deployment_dimension_filter,
        )
        for name in metric_names
    }


def deployment_filter(deployment_name: str) -> str:
    """Builds the OData filter Azure OpenAI resource metrics use to
    scope a query to one deployment. The dimension name
    ("ModelDeploymentName") is Microsoft's documented one for Azure
    OpenAI resource-level metrics — confirm it still applies via
    `list_available_metric_names()`'s dimensions before relying on it
    for a non-Azure-OpenAI resource.
    """
    return f"ModelDeploymentName eq '{deployment_name}'"


def _timedelta_to_iso8601(interval: dt.timedelta) -> str:
    total_seconds = int(interval.total_seconds())
    if total_seconds % 60 == 0:
        return f"PT{total_seconds // 60}M"
    return f"PT{total_seconds}S"
