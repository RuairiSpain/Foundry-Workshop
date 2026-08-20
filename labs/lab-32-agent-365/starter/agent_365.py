"""Registers published Agent Applications with Agent 365's control
plane, and evaluates org-wide observe / secure / govern policy over the
registered fleet.

Optional: requires Agent 365 licensing to do this against the real
admin center (Steps 2-3). The registration and policy logic below is
fully testable without it — Lab 26 already covered publishing the
Agent Applications this one registers.

Agent 365 has no public Python SDK as of writing this workshop — every
hands-on step is in the admin center (see README.md). This module
models the registration record and the policy checks that center runs,
so the *decisions* are testable even though the control plane itself
isn't.
"""

from __future__ import annotations

import dataclasses


@dataclasses.dataclass
class AgentRegistration:
    agent_app_id: str
    name: str
    owner_email: str
    data_boundary: str
    content_safety_enabled: bool
    published_version: int


def register_agent(
    *,
    agent_app_id: str,
    name: str,
    owner_email: str,
    data_boundary: str,
    content_safety_enabled: bool,
    published_version: int,
) -> AgentRegistration:
    """Builds one Agent 365 registration record for an already-published
    Agent Application (Lab 26).
    """
    # TODO: build and return the AgentRegistration.
    raise NotImplementedError


def find_unregistered_agents(all_agent_names: list[str], registrations: list[AgentRegistration]) -> list[str]:
    """Returns agent names that exist in Foundry but aren't registered,
    sorted alphabetically.
    """
    # TODO: diff all_agent_names against the registered names.
    raise NotImplementedError


def evaluate_governance_policy(
    registration: AgentRegistration, *, required_data_boundary: str, require_content_safety: bool = True
) -> list[str]:
    """Checks one registration against org policy. Returns a list of
    violation strings — empty if the registration is compliant.

    Check both the data boundary and (if require_content_safety) the
    Content Safety flag — don't stop at the first violation.
    """
    # TODO: return the list of violation strings.
    raise NotImplementedError


def build_fleet_dashboard(
    registrations: list[AgentRegistration],
    traces: list[dict],
    *,
    required_data_boundary: str,
    require_content_safety: bool = True,
) -> dict[str, dict]:
    """Builds the org-wide dashboard: per-agent trace volume, failures,
    and governance violations, for every registered agent.

    Return a dict keyed by agent name, each value a dict with
    "trace_count", "failure_count", and "governance_violations".
    """
    # TODO: build and return the dashboard dict.
    raise NotImplementedError


def main() -> None:  # pragma: no cover - real Agent 365 admin center steps, exercised manually
    fleet_traces = [
        {"trace_id": "tr-101", "agent_name": "cascadia-order-status", "duration_ms": 480, "status": "success"},
        {"trace_id": "tr-102", "agent_name": "cascadia-order-status", "duration_ms": 510, "status": "failed"},
        {"trace_id": "tr-103", "agent_name": "cascadia-trip-planner", "duration_ms": 690, "status": "success"},
        {"trace_id": "tr-104", "agent_name": "cascadia-store-ops", "duration_ms": 340, "status": "success"},
    ]
    registrations = [
        register_agent(
            agent_app_id="app-0001",
            name="cascadia-order-status",
            owner_email="maya@cascadiaoutfitters.example",
            data_boundary="US",
            content_safety_enabled=True,
            published_version=3,
        ),
        register_agent(
            agent_app_id="app-0002",
            name="cascadia-trip-planner",
            owner_email="maya@cascadiaoutfitters.example",
            data_boundary="EU",
            content_safety_enabled=False,
            published_version=1,
        ),
    ]

    unregistered = find_unregistered_agents(
        ["cascadia-order-status", "cascadia-trip-planner", "cascadia-store-ops"], registrations
    )
    print(f"Unregistered: {unregistered}")

    dashboard = build_fleet_dashboard(registrations, fleet_traces, required_data_boundary="US")
    for name, stats in dashboard.items():
        print(f"{name}: {stats}")


if __name__ == "__main__":  # pragma: no cover
    main()
