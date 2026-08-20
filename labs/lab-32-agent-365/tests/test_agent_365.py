"""Tests for solution/agent_365.py.

main() is excluded from coverage — it's a printout of the same logic
these tests already exercise, meant for a live Agent 365 admin center
walkthrough.
"""

from solution.agent_365 import (
    build_fleet_dashboard,
    evaluate_governance_policy,
    find_unregistered_agents,
    register_agent,
)


def make_registration(**overrides):
    defaults = dict(
        agent_app_id="app-0001",
        name="cascadia-order-status",
        owner_email="maya@cascadiaoutfitters.example",
        data_boundary="US",
        content_safety_enabled=True,
        published_version=3,
    )
    defaults.update(overrides)
    return register_agent(**defaults)


def test_register_agent_builds_the_registration_record():
    registration = make_registration()

    assert registration.agent_app_id == "app-0001"
    assert registration.name == "cascadia-order-status"
    assert registration.published_version == 3


def test_find_unregistered_agents_returns_the_gap_sorted():
    registrations = [make_registration(name="cascadia-order-status")]

    unregistered = find_unregistered_agents(
        ["cascadia-trip-planner", "cascadia-order-status", "cascadia-store-ops"], registrations
    )

    assert unregistered == ["cascadia-store-ops", "cascadia-trip-planner"]


def test_find_unregistered_agents_returns_empty_when_everything_is_registered():
    registrations = [make_registration(name="cascadia-order-status")]

    unregistered = find_unregistered_agents(["cascadia-order-status"], registrations)

    assert unregistered == []


def test_evaluate_governance_policy_passes_a_compliant_registration():
    registration = make_registration(data_boundary="US", content_safety_enabled=True)

    violations = evaluate_governance_policy(registration, required_data_boundary="US")

    assert violations == []


def test_evaluate_governance_policy_flags_the_wrong_data_boundary():
    registration = make_registration(data_boundary="EU", content_safety_enabled=True)

    violations = evaluate_governance_policy(registration, required_data_boundary="US")

    assert any("data boundary" in violation for violation in violations)


def test_evaluate_governance_policy_flags_content_safety_disabled():
    registration = make_registration(data_boundary="US", content_safety_enabled=False)

    violations = evaluate_governance_policy(registration, required_data_boundary="US")

    assert any("Content Safety" in violation for violation in violations)


def test_evaluate_governance_policy_can_skip_the_content_safety_check():
    registration = make_registration(data_boundary="US", content_safety_enabled=False)

    violations = evaluate_governance_policy(registration, required_data_boundary="US", require_content_safety=False)

    assert violations == []


def test_evaluate_governance_policy_reports_both_violations_at_once():
    registration = make_registration(data_boundary="EU", content_safety_enabled=False)

    violations = evaluate_governance_policy(registration, required_data_boundary="US")

    assert len(violations) == 2


def test_build_fleet_dashboard_aggregates_traces_and_violations_per_agent():
    registrations = [
        make_registration(name="cascadia-order-status", data_boundary="US", content_safety_enabled=True),
        make_registration(name="cascadia-trip-planner", data_boundary="EU", content_safety_enabled=False),
    ]
    traces = [
        {"trace_id": "tr-1", "agent_name": "cascadia-order-status", "status": "success"},
        {"trace_id": "tr-2", "agent_name": "cascadia-order-status", "status": "failed"},
        {"trace_id": "tr-3", "agent_name": "cascadia-trip-planner", "status": "success"},
    ]

    dashboard = build_fleet_dashboard(registrations, traces, required_data_boundary="US")

    assert dashboard["cascadia-order-status"]["trace_count"] == 2
    assert dashboard["cascadia-order-status"]["failure_count"] == 1
    assert dashboard["cascadia-order-status"]["governance_violations"] == []
    assert dashboard["cascadia-trip-planner"]["trace_count"] == 1
    assert len(dashboard["cascadia-trip-planner"]["governance_violations"]) == 2


def test_build_fleet_dashboard_handles_a_registered_agent_with_no_traces():
    registrations = [make_registration(name="cascadia-store-ops", data_boundary="US", content_safety_enabled=True)]

    dashboard = build_fleet_dashboard(registrations, traces=[], required_data_boundary="US")

    assert dashboard["cascadia-store-ops"]["trace_count"] == 0
    assert dashboard["cascadia-store-ops"]["failure_count"] == 0
