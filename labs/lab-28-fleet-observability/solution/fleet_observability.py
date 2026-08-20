"""Analyzes a batch of trace records to find the expensive, slow, and
failing agents across the Cascadia fleet — the same triage a KQL query
against Log Analytics does, run here over a local dataset so the
analysis logic is testable without a live workspace. See README.md for
the equivalent KQL.
"""

from __future__ import annotations

import dataclasses

# A synthetic snapshot of one hour's traces across the fleet, standing
# in for what Lab 28's Portal step pulls from Azure Monitor. Includes
# one planted cost spike (concierge, web search on a long question), one
# planted latency regression (trip-planner, an unusually slow run), and
# one planted failure (order, a tool call error) — the three things this
# lab exists to find.
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
    slow = [trace for trace in traces if trace["duration_ms"] > threshold_ms]
    return sorted(slow, key=lambda trace: trace["duration_ms"], reverse=True)


def find_expensive_traces(traces: list[dict], *, threshold_usd: float) -> list[dict]:
    """Returns traces costing more than threshold_usd, most expensive first."""
    expensive = [trace for trace in traces if trace["cost_usd"] > threshold_usd]
    return sorted(expensive, key=lambda trace: trace["cost_usd"], reverse=True)


def find_failed_traces(traces: list[dict]) -> list[dict]:
    """Returns every trace with a non-success status."""
    return [trace for trace in traces if trace["status"] != "success"]


@dataclasses.dataclass
class AgentStats:
    agent_name: str
    trace_count: int
    total_cost_usd: float
    average_duration_ms: float
    failure_rate: float


def summarize_by_agent(traces: list[dict]) -> dict[str, AgentStats]:
    """Aggregates cost, latency, and failure rate per agent — the
    fleet-wide view a cost or latency spike starts from, before you
    drill into any one trace.
    """
    by_agent: dict[str, list[dict]] = {}
    for trace in traces:
        by_agent.setdefault(trace["agent_name"], []).append(trace)

    summary: dict[str, AgentStats] = {}
    for agent_name, agent_traces in by_agent.items():
        failures = sum(1 for trace in agent_traces if trace["status"] != "success")
        summary[agent_name] = AgentStats(
            agent_name=agent_name,
            trace_count=len(agent_traces),
            total_cost_usd=sum(trace["cost_usd"] for trace in agent_traces),
            average_duration_ms=sum(trace["duration_ms"] for trace in agent_traces) / len(agent_traces),
            failure_rate=failures / len(agent_traces),
        )
    return summary


def correlate_metric_to_trace(traces: list[dict], *, trace_id: str) -> dict:
    """Jumps from a metric — a trace ID a dashboard flagged — straight to
    the full trace record, with no manual timestamp correlation.

    Raises KeyError if the trace_id doesn't exist, since a dashboard
    pointing at a trace that isn't in the data is worth failing loudly
    on, not silently returning None for.
    """
    for trace in traces:
        if trace["trace_id"] == trace_id:
            return trace
    raise KeyError(f"No trace found with ID {trace_id!r}")


def main() -> None:  # pragma: no cover - real Azure Monitor query, exercised manually
    slow = find_slow_traces(FLEET_TRACES, threshold_ms=2000)
    expensive = find_expensive_traces(FLEET_TRACES, threshold_usd=0.1)
    failed = find_failed_traces(FLEET_TRACES)
    print(f"Slow: {[t['trace_id'] for t in slow]}")
    print(f"Expensive: {[t['trace_id'] for t in expensive]}")
    print(f"Failed: {[t['trace_id'] for t in failed]}")
    for stats in summarize_by_agent(FLEET_TRACES).values():
        print(stats)


if __name__ == "__main__":  # pragma: no cover
    main()
