"""Builds Cascadia's Trip Planner as a Microsoft Agent Framework agent
against the hub's shared Foundry model, with one custom tool.
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
    """Suggest gear for a named trail from Cascadia's trail database."""
    # TODO(lab-12): look up trail_name in load_trail_database(). If it's
    # missing, return a string listing the known trail names instead.
    # Otherwise return a plain-language string with the difficulty,
    # distance, and a comma-joined list of recommended_gear.
    raise NotImplementedError("suggest_gear_for_trail is not implemented yet")


def build_trip_planner_agent(client) -> Agent:
    """Builds the Trip Planner as a single Microsoft Agent Framework agent."""
    # TODO(lab-12): return an Agent built from `client`, with a name,
    # instructions telling it to ground gear recommendations in the
    # tool's output, and tools=[suggest_gear_for_trail]. Name the
    # suggest_gear_for_trail tool by its exact function name somewhere
    # in the instructions text — that's what tells the model which tool
    # to call.
    raise NotImplementedError("build_trip_planner_agent is not implemented yet")


def main() -> None:
    import asyncio
    import os

    from agent_framework.foundry import FoundryChatClient
    from azure.identity import DefaultAzureCredential

    client = FoundryChatClient(
        project_endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"],
        model=os.environ.get("LOW_COST_DEPLOYMENT", "cascadia-low-cost"),
        credential=DefaultAzureCredential(),
    )
    agent = build_trip_planner_agent(client)
    response = asyncio.run(agent.run("Plan gear for the Cascade Pass Loop."))
    print(response.text)


if __name__ == "__main__":
    main()
