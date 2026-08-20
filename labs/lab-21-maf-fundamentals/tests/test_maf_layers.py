"""Tests for solution/maf_layers.py.

main() is excluded from coverage — real SDK wiring, live model calls,
and a CLI entry point, exercised manually, not under test.

None of these tests call `.run()` on anything: Agent and Workflow are
both built synchronously, so their shape is inspectable without a live
model — the same approach Lab 12 used.
"""

from solution.maf_layers import build_agent_loop, build_harness_agent, build_workflow, suggest_gear_for_trail


def test_suggest_gear_for_trail_describes_a_known_trail():
    result = suggest_gear_for_trail("Rattlesnake Ledge")

    assert "easy" in result
    assert "Trail Boot" in result


def test_suggest_gear_for_trail_lists_known_trails_for_an_unknown_one():
    result = suggest_gear_for_trail("Mount Doom")

    assert "No trail data" in result
    assert "Rattlesnake Ledge" in result


def test_build_agent_loop_has_the_expected_name_and_tool():
    agent = build_agent_loop(object())

    assert agent.name == "cascadia-trip-planner"
    assert agent.default_options["tools"][0].name == "suggest_gear_for_trail"


def test_build_agent_loop_is_a_plain_agent_with_no_harness_middleware():
    agent = build_agent_loop(object())

    assert not agent.middleware
    assert not agent.context_providers


def test_build_workflow_wraps_the_same_agent():
    workflow = build_workflow(object())

    executors = workflow.get_executors_list()
    agent_executors = [executor for executor in executors if hasattr(executor, "agent")]
    assert len(agent_executors) == 1
    assert agent_executors[0].agent.name == "cascadia-trip-planner"


def test_build_harness_agent_has_the_expected_name_and_tool():
    agent = build_harness_agent(object())

    assert agent.name == "cascadia-trip-planner-harness"
    tool_names = {tool.name for tool in agent.default_options.get("tools", [])}
    assert "suggest_gear_for_trail" in tool_names


def test_build_harness_agent_has_harness_middleware_a_plain_agent_does_not():
    harness_agent = build_harness_agent(object())
    loop_agent = build_agent_loop(object())

    assert len(harness_agent.middleware) > 0
    assert len(harness_agent.context_providers) > 0
    assert not loop_agent.middleware
