"""Tests for solution/orchestration_patterns.py.

main() is excluded from coverage — real SDK wiring, a live model call
through a Magentic run, and a CLI entry point, exercised manually, not
under test.

None of these tests call `.run()` on a workflow: every builder's
`.build()` is synchronous, so a workflow's participants are inspectable
through `get_executors_list()` without a live model.
"""

from solution.orchestration_patterns import (
    build_concurrent_workflow,
    build_handoff_workflow,
    build_magentic_workflow,
    build_sequential_workflow,
)


def _agent_names(workflow) -> list[str]:
    return [executor.agent.name for executor in workflow.get_executors_list() if hasattr(executor, "agent")]


def test_sequential_workflow_runs_triage_then_order_in_order():
    workflow = build_sequential_workflow(object())

    assert _agent_names(workflow) == ["triage", "order"]


def test_concurrent_workflow_includes_order_and_trip_planner():
    workflow = build_concurrent_workflow(object())

    assert set(_agent_names(workflow)) == {"order", "trip-planner"}


def test_handoff_workflow_includes_triage_and_order():
    workflow = build_handoff_workflow(object())

    assert set(_agent_names(workflow)) == {"triage", "order"}


def test_magentic_workflow_includes_all_four_specialists():
    workflow = build_magentic_workflow(object())

    assert set(_agent_names(workflow)) == {"triage", "order", "trip-planner", "innovation"}


def test_magentic_workflow_includes_exactly_one_manager_executor():
    workflow = build_magentic_workflow(object())

    manager_executors = [
        executor for executor in workflow.get_executors_list() if type(executor).__name__ == "MagenticOrchestrator"
    ]
    assert len(manager_executors) == 1
