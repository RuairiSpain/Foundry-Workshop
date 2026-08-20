"""Cascadia's Trip Planner delegates shipping-ETA questions to
SwiftShip over A2A, instead of implementing shipping logic itself.
"""

from __future__ import annotations

from agent_framework import Agent
from agent_framework.a2a import A2AAgent


def build_swiftship_client(url: str) -> A2AAgent:
    """Builds the client-side handle to the SwiftShip partner agent."""
    # TODO(lab-25): return an A2AAgent with name="swiftship", the given
    # url, and a description.
    raise NotImplementedError("build_swiftship_client is not implemented yet")


def build_trip_planner_with_swiftship(client, *, swiftship_url: str) -> Agent:
    """Builds a Trip Planner that delegates shipping-ETA questions to
    SwiftShip instead of answering them itself.
    """
    # TODO(lab-25): build the SwiftShip client with build_swiftship_client(),
    # then return an Agent with tools=[swiftship.as_tool()].
    raise NotImplementedError("build_trip_planner_with_swiftship is not implemented yet")


def main() -> None:
    import asyncio
    import os

    from agent_framework.foundry import FoundryChatClient

    client = FoundryChatClient(
        project_endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"],
        model=os.environ.get("LOW_COST_DEPLOYMENT", "cascadia-low-cost"),
    )
    trip_planner = build_trip_planner_with_swiftship(
        client, swiftship_url=os.environ.get("SWIFTSHIP_A2A_URL", "http://localhost:8001/a2a")
    )
    response = asyncio.run(
        trip_planner.run("How long will shipping take from pacific-northwest to national?")
    )
    print(response.text)


if __name__ == "__main__":
    main()
