"""Azure Monitor querying tolerates missing/unavailable metrics rather
than treating the whole query as failed (spec 2.9, 2.13).
"""

from __future__ import annotations

import datetime as dt

from src.azure_monitor import (
    build_resource_id,
    deployment_filter,
    list_available_metric_names,
    query_metric,
    query_metrics_for_window,
)


class _FakeMetricDefinitionsOps:
    def __init__(self, names, *, raise_error=False):
        self._names = names
        self._raise_error = raise_error

    def list(self, resource_uri, metricnamespace=None):
        if self._raise_error:
            raise RuntimeError("ARM call failed")
        return [_FakeDefinition(name) for name in self._names]


class _FakeDefinition:
    def __init__(self, name):
        from types import SimpleNamespace

        self.name = SimpleNamespace(value=name)


class _FakeMetricsOps:
    def __init__(self, *, metric_response=None, raise_error=False):
        self._metric_response = metric_response
        self._raise_error = raise_error
        self.calls = []

    def list(self, **kwargs):
        self.calls.append(kwargs)
        if self._raise_error:
            raise RuntimeError("metric not supported for this resource")
        return self._metric_response


class _FakeMonitorClient:
    def __init__(self, *, metric_definitions=None, metrics=None):
        self.metric_definitions = metric_definitions
        self.metrics = metrics


def test_build_resource_id_shape():
    resource_id = build_resource_id(subscription_id="sub-1", resource_group="rg-1", foundry_resource_name="res-1")
    assert resource_id == "/subscriptions/sub-1/resourceGroups/rg-1/providers/Microsoft.CognitiveServices/accounts/res-1"


def test_deployment_filter_shape():
    assert deployment_filter("my-deployment") == "ModelDeploymentName eq 'my-deployment'"


def test_list_available_metric_names_happy_path():
    client = _FakeMonitorClient(metric_definitions=_FakeMetricDefinitionsOps(["A", "B", "C"]))
    names = list_available_metric_names(client, "resource-id")
    assert names == {"A", "B", "C"}


def test_list_available_metric_names_tolerates_failure_and_returns_empty_set():
    """spec 2.9: enumeration failing must not raise — it degrades to
    "query nothing extra", not an aborted run.
    """
    client = _FakeMonitorClient(metric_definitions=_FakeMetricDefinitionsOps([], raise_error=True))
    names = list_available_metric_names(client, "resource-id")
    assert names == set()


def _fake_metric_response(*, unit="Count", total_values=(100.0,)):
    from types import SimpleNamespace

    data_points = [
        SimpleNamespace(time_stamp=dt.datetime(2026, 1, 1), average=value, total=value, count=1, minimum=value, maximum=value)
        for value in total_values
    ]
    metric = SimpleNamespace(unit=unit, timeseries=[SimpleNamespace(data=data_points)])
    return SimpleNamespace(value=[metric])


def test_query_metric_happy_path_sums_and_averages_correctly():
    client = _FakeMonitorClient(metrics=_FakeMetricsOps(metric_response=_fake_metric_response(total_values=(10.0, 20.0, 30.0))))
    result = query_metric(
        client, "resource-id", "Processed Prompt Tokens", start=dt.datetime(2026, 1, 1), end=dt.datetime(2026, 1, 1, 1)
    )
    assert result.available
    assert result.sum_total() == 60.0
    assert result.average_of_averages() == 20.0


def test_query_metric_tolerates_a_failure_and_marks_unavailable():
    client = _FakeMonitorClient(metrics=_FakeMetricsOps(raise_error=True))
    result = query_metric(client, "resource-id", "SomeUnsupportedMetric", start=dt.datetime(2026, 1, 1), end=dt.datetime(2026, 1, 1, 1))
    assert not result.available
    assert result.error is not None
    assert result.sum_total() is None


def test_query_metric_handles_no_data_returned():
    from types import SimpleNamespace

    client = _FakeMonitorClient(metrics=_FakeMetricsOps(metric_response=SimpleNamespace(value=[])))
    result = query_metric(client, "resource-id", "SomeMetric", start=dt.datetime(2026, 1, 1), end=dt.datetime(2026, 1, 1, 1))
    assert not result.available


def test_query_metrics_for_window_queries_each_metric_independently():
    """One unsupported metric name among several must not prevent the
    others from being queried — the ARM API rejects an entire batched
    request over a single bad name, so each metric goes out as its own
    call.
    """

    class _SelectiveMetricsOps:
        def list(self, **kwargs):
            if kwargs["metricnames"] == "BadMetric":
                raise RuntimeError("unsupported metric")
            return _fake_metric_response(total_values=(5.0,))

    client = _FakeMonitorClient(metrics=_SelectiveMetricsOps())
    results = query_metrics_for_window(
        client,
        "resource-id",
        ["GoodMetric", "BadMetric"],
        start=dt.datetime(2026, 1, 1),
        end=dt.datetime(2026, 1, 1, 1),
    )
    assert results["GoodMetric"].available
    assert not results["BadMetric"].available
    assert set(results.keys()) == {"GoodMetric", "BadMetric"}  # both present, one just unavailable


def test_query_metric_passes_deployment_filter_through():
    ops = _FakeMetricsOps(metric_response=_fake_metric_response())
    client = _FakeMonitorClient(metrics=ops)
    query_metric(
        client,
        "resource-id",
        "Processed Prompt Tokens",
        start=dt.datetime(2026, 1, 1),
        end=dt.datetime(2026, 1, 1, 1),
        deployment_dimension_filter=deployment_filter("my-deployment"),
    )
    assert ops.calls[0]["filter"] == "ModelDeploymentName eq 'my-deployment'"
