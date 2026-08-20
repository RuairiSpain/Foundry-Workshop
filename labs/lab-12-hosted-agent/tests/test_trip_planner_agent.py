"""Tests for solution/trip_planner_agent.py.

main() is excluded from coverage — real SDK wiring, a live model call,
and a CLI entry point, exercised manually, not under test.

build_trip_planner_agent() is checked without a live model call: the
Agent constructor is synchronous and just stores what you pass it, so
its instructions and tools are inspectable through `default_options`
without ever calling `.run()`.
"""

from solution.trip_planner_agent import build_trip_planner_agent, load_trail_database, suggest_gear_for_trail


def test_load_trail_database_has_the_three_case_study_trails():
    trails = load_trail_database()

    assert set(trails) == {"Cascade Pass Loop", "Skyline Divide", "Rattlesnake Ledge"}


def test_suggest_gear_for_trail_describes_a_known_trail():
    result = suggest_gear_for_trail("Cascade Pass Loop")

    assert "moderate" in result
    assert "12.5" in result
    assert "Trail Boot" in result


def test_suggest_gear_for_trail_lists_known_trails_for_an_unknown_one():
    result = suggest_gear_for_trail("Mount Doom")

    assert "No trail data" in result
    assert "Cascade Pass Loop" in result


def test_build_trip_planner_agent_sets_the_expected_name():
    agent = build_trip_planner_agent(client=object())

    assert agent.name == "cascadia-trip-planner"


def test_build_trip_planner_agent_instructions_mention_the_tool():
    agent = build_trip_planner_agent(client=object())

    assert "suggest_gear_for_trail" in agent.default_options["instructions"]


def test_build_trip_planner_agent_registers_the_tool():
    agent = build_trip_planner_agent(client=object())

    tools = agent.default_options["tools"]
    assert len(tools) == 1
    assert tools[0].name == "suggest_gear_for_trail"
