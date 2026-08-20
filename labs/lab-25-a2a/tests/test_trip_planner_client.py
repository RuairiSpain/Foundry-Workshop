"""Tests for solution/trip_planner_client.py.

main() is excluded from coverage — real SDK wiring, a live A2A call,
and a CLI entry point, exercised manually, not under test.

Neither test makes a network call: A2AAgent's constructor is lazy, the
same pattern as FoundryChatClient and GitHubCopilotAgent, so it's
inspectable without contacting SwiftShip.
"""

from solution.trip_planner_client import build_swiftship_client, build_trip_planner_with_swiftship


def test_build_swiftship_client_points_at_the_given_url():
    client = build_swiftship_client("http://localhost:8001/a2a")

    assert client.name == "swiftship"


def test_build_trip_planner_with_swiftship_has_the_delegation_tool():
    agent = build_trip_planner_with_swiftship(object(), swiftship_url="http://localhost:8001/a2a")

    tool_names = {tool.name for tool in agent.default_options["tools"]}
    assert tool_names == {"swiftship"}


def test_build_trip_planner_with_swiftship_instructions_mention_delegating():
    agent = build_trip_planner_with_swiftship(object(), swiftship_url="http://localhost:8001/a2a")

    assert "delegate" in agent.default_options["instructions"].lower()
