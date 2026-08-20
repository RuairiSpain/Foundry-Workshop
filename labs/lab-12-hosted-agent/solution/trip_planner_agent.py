"""Builds Cascadia's Trip Planner as a Microsoft Agent Framework agent
against the hub's shared Foundry model, with one custom tool.

This is deliberately a single, simple agent. Module 6 (Labs 21-25)
returns to Microsoft Agent Framework and builds multi-agent workflows,
an alternate harness, durable execution, and cross-process delegation on
top of the same Agent class you use here.
"""

from __future__ import annotations

import json
from pathlib import Path

from agent_framework import Agent

TRAIL_DATABASE_PATH = Path(__file__).resolve().parents[3] / "case-study" / "trail-database.json"


def load_trail_database(path: Path = TRAIL_DATABASE_PATH) -> dict:
    with path.open() as trail_file:
        return json.load(trail_file)


def suggest_gear_for_trail(trail_name: str) -> str:
    """Suggest gear for a named trail from Cascadia's trail database.

    Returns a plain-language string, not a data structure — MAF hands a
    tool's return value straight back to the model as the tool result,
    so the model reads this the same way it would read a person's reply.
    """
    trails = load_trail_database()
    trail = trails.get(trail_name)
    if trail is None:
        known = ", ".join(trails)
        return f"No trail data for {trail_name!r}. Known trails: {known}."
    gear = ", ".join(trail["recommended_gear"])
    return f"For {trail_name} ({trail['difficulty']}, {trail['distance_km']} km): {gear}."


def build_trip_planner_agent(client) -> Agent:
    """Builds the Trip Planner as a single Microsoft Agent Framework agent."""
    return Agent(
        client,
        name="cascadia-trip-planner",
        instructions=(
            "You help Cascadia Outfitters customers plan hikes. Use the "
            "suggest_gear_for_trail tool to ground gear recommendations in "
            "real trail data — never invent a trail's difficulty or distance."
        ),
        tools=[suggest_gear_for_trail],
    )


def main() -> None:  # pragma: no cover - real SDK wiring and CLI entry point, exercised manually
    import asyncio
    import os

    from agent_framework.foundry import FoundryChatClient

    client = FoundryChatClient(
        project_endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"],
        model=os.environ.get("LOW_COST_DEPLOYMENT", "cascadia-low-cost"),
    )
    agent = build_trip_planner_agent(client)
    response = asyncio.run(agent.run("Plan gear for the Cascade Pass Loop."))
    print(response.text)


if __name__ == "__main__":  # pragma: no cover
    main()
