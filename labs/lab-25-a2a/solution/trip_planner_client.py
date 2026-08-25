"""Cascadia's Trip Planner delegates shipping-ETA questions to
SwiftShip over A2A, instead of implementing shipping logic itself.
"""

from __future__ import annotations

from agent_framework import Agent
from agent_framework.a2a import A2AAgent


def build_swiftship_client(url: str) -> A2AAgent:
    """Builds the client-side handle to the SwiftShip partner agent.

    No network call happens here — the same lazy-construction pattern
    every other client in this workshop uses (FoundryChatClient,
    GitHubCopilotAgent).
    """
    return A2AAgent(name="swiftship", url=url, description="SwiftShip's shipping ETA lookup, over A2A.")


def build_trip_planner_with_swiftship(client, *, swiftship_url: str) -> Agent:
    """Builds a Trip Planner that delegates shipping-ETA questions to
    SwiftShip instead of answering them itself.
    """
    swiftship = build_swiftship_client(swiftship_url)
    return Agent(
        client,
        name="cascadia-trip-planner",
        instructions=(
            "You help Cascadia customers plan hikes and track shipments. "
            "Delegate any shipping ETA question to the swiftship tool — "
            "you don't have shipping data yourself."
        ),
        tools=[swiftship.as_tool()],
    )


def main() -> None:  # pragma: no cover - real SDK wiring, a live A2A call, and a CLI entry point, exercised manually
    import asyncio
    import os

    from agent_framework.foundry import FoundryChatClient
    from azure.identity import DefaultAzureCredential

    client = FoundryChatClient(
        project_endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"],
        model=os.environ.get("LOW_COST_DEPLOYMENT", "cascadia-low-cost"),
        credential=DefaultAzureCredential(),
    )
    trip_planner = build_trip_planner_with_swiftship(
        client, swiftship_url=os.environ.get("SWIFTSHIP_A2A_URL", "http://localhost:8001/a2a")
    )
    response = asyncio.run(
        trip_planner.run("How long will shipping take from pacific-northwest to national?")
    )
    print(response.text)


if __name__ == "__main__":  # pragma: no cover
    main()
