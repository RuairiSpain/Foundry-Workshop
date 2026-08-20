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

    Registration doesn't publish or change the agent — it's a separate,
    additive step that puts an already-live agent under Agent 365's
    control plane.
    """
    return AgentRegistration(
        agent_app_id=agent_app_id,
        name=name,
        owner_email=owner_email,
        data_boundary=data_boundary,
        content_safety_enabled=content_safety_enabled,
        published_version=published_version,
    )


def find_unregistered_agents(all_agent_names: list[str], registrations: list[AgentRegistration]) -> list[str]:
    """Returns agent names that exist in Foundry but aren't registered.

    An unregistered agent is invisible to Agent 365's org-wide view —
    this is the gap the "observe" pillar exists to close: it can only
    watch what's registered.
    """
    registered_names = {registration.name for registration in registrations}
    return sorted(set(all_agent_names) - registered_names)


def evaluate_governance_policy(
    registration: AgentRegistration, *, required_data_boundary: str, require_content_safety: bool = True
) -> list[str]:
    """Checks one registration against org policy. Returns a list of
    violation strings — empty if the registration is compliant.

    Checks every rule rather than stopping at the first violation, so
    an admin sees the full list to fix in one pass instead of
    discovering the second problem only after fixing the first.
    """
    violations = []
    if registration.data_boundary != required_data_boundary:
        violations.append(
            f"{registration.name}: data boundary is {registration.data_boundary!r}, "
            f"org policy requires {required_data_boundary!r}"
        )
    if require_content_safety and not registration.content_safety_enabled:
        violations.append(f"{registration.name}: Content Safety is not enabled")
    return violations


def build_fleet_dashboard(
    registrations: list[AgentRegistration],
    traces: list[dict],
    *,
    required_data_boundary: str,
    require_content_safety: bool = True,
) -> dict[str, dict]:
    """Builds the org-wide dashboard: per-agent trace volume, failures,
    and governance violations, for every registered agent.

    Keyed by agent name so an admin can spot, at a glance, which
    registered agents are both busy and out of policy — the two facts
    Agent 365 exists to put on one screen.
    """
    dashboard: dict[str, dict] = {}
    for registration in registrations:
        agent_traces = [trace for trace in traces if trace["agent_name"] == registration.name]
        dashboard[registration.name] = {
            "trace_count": len(agent_traces),
            "failure_count": sum(1 for trace in agent_traces if trace["status"] != "success"),
            "governance_violations": evaluate_governance_policy(
                registration,
                required_data_boundary=required_data_boundary,
                require_content_safety=require_content_safety,
            ),
        }
    return dashboard


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
