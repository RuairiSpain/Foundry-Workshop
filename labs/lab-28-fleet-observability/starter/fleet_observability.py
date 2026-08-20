"""Analyzes a batch of trace records to find the expensive, slow, and
failing agents across the Cascadia fleet.
"""

from __future__ import annotations

import dataclasses

# A synthetic snapshot of one hour's traces across the fleet. Includes
# one planted cost spike (concierge), one planted latency regression
# (trip-planner), and one planted failure (order) — the three things
# this lab exists to find.
FLEET_TRACES: list[dict] = [
    {"trace_id": "tr-001", "agent_name": "cascadia-support", "duration_ms": 420, "cost_usd": 0.004, "status": "success"},
    {"trace_id": "tr-002", "agent_name": "cascadia-support", "duration_ms": 380, "cost_usd": 0.003, "status": "success"},
    {"trace_id": "tr-003", "agent_name": "cascadia-order-status", "duration_ms": 510, "cost_usd": 0.005, "status": "success"},
    {"trace_id": "tr-004", "agent_name": "cascadia-order-status", "duration_ms": 490, "cost_usd": 0.005, "status": "failed"},
    {"trace_id": "tr-005", "agent_name": "cascadia-concierge", "duration_ms": 610, "cost_usd": 0.312, "status": "success"},
    {"trace_id": "tr-006", "agent_name": "cascadia-concierge", "duration_ms": 590, "cost_usd": 0.009, "status": "success"},
    {"trace_id": "tr-007", "agent_name": "cascadia-trip-planner", "duration_ms": 7840, "cost_usd": 0.011, "status": "success"},
    {"trace_id": "tr-008", "agent_name": "cascadia-trip-planner", "duration_ms": 720, "cost_usd": 0.010, "status": "success"},
]


def find_slow_traces(traces: list[dict], *, threshold_ms: float) -> list[dict]:
    """Returns traces slower than threshold_ms, slowest first."""
    # TODO(lab-28): filter traces to duration_ms > threshold_ms, and
    # sort them slowest first.
    raise NotImplementedError("find_slow_traces is not implemented yet")


def find_expensive_traces(traces: list[dict], *, threshold_usd: float) -> list[dict]:
    """Returns traces costing more than threshold_usd, most expensive first."""
    # TODO(lab-28): filter traces to cost_usd > threshold_usd, and sort
    # them most expensive first.
    raise NotImplementedError("find_expensive_traces is not implemented yet")


def find_failed_traces(traces: list[dict]) -> list[dict]:
    """Returns every trace with a non-success status."""
    # TODO(lab-28): filter traces to status != "success".
    raise NotImplementedError("find_failed_traces is not implemented yet")


@dataclasses.dataclass
class AgentStats:
    agent_name: str
    trace_count: int
    total_cost_usd: float
    average_duration_ms: float
    failure_rate: float


def summarize_by_agent(traces: list[dict]) -> dict[str, AgentStats]:
    """Aggregates cost, latency, and failure rate per agent."""
    # TODO(lab-28): group traces by agent_name, then build an AgentStats
    # per agent with trace_count, total_cost_usd, average_duration_ms,
    # and failure_rate (fraction of non-success traces).
    raise NotImplementedError("summarize_by_agent is not implemented yet")


def correlate_metric_to_trace(traces: list[dict], *, trace_id: str) -> dict:
    """Jumps from a metric — a trace ID a dashboard flagged — straight
    to the full trace record.
    """
    # TODO(lab-28): find the trace with this trace_id and return it.
    # Raise KeyError if none matches.
    raise NotImplementedError("correlate_metric_to_trace is not implemented yet")


def main() -> None:
    slow = find_slow_traces(FLEET_TRACES, threshold_ms=2000)
    expensive = find_expensive_traces(FLEET_TRACES, threshold_usd=0.1)
    failed = find_failed_traces(FLEET_TRACES)
    print(f"Slow: {[t['trace_id'] for t in slow]}")
    print(f"Expensive: {[t['trace_id'] for t in expensive]}")
    print(f"Failed: {[t['trace_id'] for t in failed]}")
    for stats in summarize_by_agent(FLEET_TRACES).values():
        print(stats)


if __name__ == "__main__":
    main()
