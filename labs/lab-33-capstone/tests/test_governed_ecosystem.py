"""Tests for solution/governed_ecosystem.py.

main() is excluded from coverage — real SDK wiring, a live Magentic
run, and a CLI entry point, exercised manually.

Like Lab 22's tests, none of these call `.run()` on the workflow:
`.build()` is synchronous, so participants are inspectable through
`get_executors_list()` without a live model or client.
"""

from solution.governed_ecosystem import (
    ReleaseGateResult,
    build_fleet_manifest,
    build_governed_workflow,
    evaluate_release_gates,
    summarize_release_readiness,
)


def _agent_names(workflow) -> list[str]:
    return [executor.agent.name for executor in workflow.get_executors_list() if hasattr(executor, "agent")]


def test_governed_workflow_includes_the_four_core_specialists():
    workflow = build_governed_workflow(object())

    assert set(_agent_names(workflow)) == {"triage", "order", "trip-planner", "innovation"}


def test_governed_workflow_omits_store_ops_by_default():
    workflow = build_governed_workflow(object())

    assert "store-ops" not in _agent_names(workflow)


def test_governed_workflow_includes_store_ops_when_opted_in():
    workflow = build_governed_workflow(object(), include_store_ops=True)

    assert "store-ops" in _agent_names(workflow)


def test_governed_workflow_has_exactly_one_manager_executor():
    workflow = build_governed_workflow(object())

    manager_executors = [
        executor for executor in workflow.get_executors_list() if type(executor).__name__ == "MagenticOrchestrator"
    ]
    assert len(manager_executors) == 1


def test_fleet_manifest_defaults_to_the_five_core_components():
    fleet = build_fleet_manifest()

    assert [component.name for component in fleet] == ["manager", "triage", "order", "trip-planner", "innovation"]
    assert all(not component.optional for component in fleet)


def test_fleet_manifest_adds_store_ops_and_teams_channel_when_included():
    fleet = build_fleet_manifest(include_store_ops=True, include_teams_channel=True)

    names = [component.name for component in fleet]
    assert names == ["manager", "triage", "order", "trip-planner", "innovation", "store-ops", "teams-channel"]
    optional_names = {component.name for component in fleet if component.optional}
    assert optional_names == {"store-ops", "teams-channel"}


def test_evaluate_release_gates_clears_a_clean_release():
    result = evaluate_release_gates(
        eval_score=0.92,
        eval_threshold=0.8,
        content_safety_violations=[],
        network_problems=[],
        governance_violations=[],
    )

    assert result == ReleaseGateResult(cleared=True, blocking_reasons=[])


def test_evaluate_release_gates_blocks_on_a_low_eval_score():
    result = evaluate_release_gates(
        eval_score=0.5,
        eval_threshold=0.8,
        content_safety_violations=[],
        network_problems=[],
        governance_violations=[],
    )

    assert result.cleared is False
    assert any("Evaluation score" in reason for reason in result.blocking_reasons)


def test_evaluate_release_gates_collects_every_reason_at_once():
    result = evaluate_release_gates(
        eval_score=0.5,
        eval_threshold=0.8,
        content_safety_violations=["hate severity 4"],
        network_problems=["public_network_access is Enabled"],
        governance_violations=["cascadia-trip-planner: data boundary is 'EU', org policy requires 'US'"],
    )

    assert result.cleared is False
    assert len(result.blocking_reasons) == 4
    assert any(reason.startswith("Content Safety: ") for reason in result.blocking_reasons)
    assert any(reason.startswith("Network: ") for reason in result.blocking_reasons)
    assert any(reason.startswith("Governance: ") for reason in result.blocking_reasons)


def test_summarize_release_readiness_when_cleared():
    fleet = build_fleet_manifest()
    result = ReleaseGateResult(cleared=True, blocking_reasons=[])

    summary = summarize_release_readiness(result, fleet)

    assert summary == "CLEARED to release. Fleet: manager, triage, order, trip-planner, innovation."


def test_summarize_release_readiness_when_blocked_lists_every_reason():
    fleet = build_fleet_manifest()
    result = ReleaseGateResult(cleared=False, blocking_reasons=["Network: public access enabled", "Governance: x"])

    summary = summarize_release_readiness(result, fleet)

    assert summary.startswith("BLOCKED. Fleet: manager, triage, order, trip-planner, innovation.\n")
    assert "  - Network: public access enabled" in summary
    assert "  - Governance: x" in summary
