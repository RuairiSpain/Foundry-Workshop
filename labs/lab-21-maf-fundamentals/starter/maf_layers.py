"""Introduces Microsoft Agent Framework's three layers — agent loop,
workflow, harness — by building Lab 12's Trip Planner all three ways.
"""

from __future__ import annotations

import json
from pathlib import Path

from agent_framework import Agent, create_harness_agent
from agent_framework.orchestrations import SequentialBuilder

TRAIL_DATABASE_PATH = Path(__file__).resolve().parents[3] / "case-study" / "trail-database.json"


def load_trail_database(path: Path = TRAIL_DATABASE_PATH) -> dict:
    with path.open() as trail_file:
        return json.load(trail_file)


def suggest_gear_for_trail(trail_name: str) -> str:
    """Same tool as Lab 12, redefined here so this lab stays self-contained."""
    trails = load_trail_database()
    trail = trails.get(trail_name)
    if trail is None:
        known = ", ".join(trails)
        return f"No trail data for {trail_name!r}. Known trails: {known}."
    gear = ", ".join(trail["recommended_gear"])
    return f"For {trail_name} ({trail['difficulty']}, {trail['distance_km']} km): {gear}."


def build_agent_loop(client) -> Agent:
    """Layer 1: the agent loop — one agent, one reasoning/act cycle per call."""
    # TODO(lab-21): return an Agent built from client, with a name,
    # instructions, and tools=[suggest_gear_for_trail].
    raise NotImplementedError("build_agent_loop is not implemented yet")


def build_workflow(client):
    """Layer 2: a workflow wrapping the same agent loop."""
    # TODO(lab-21): build the agent with build_agent_loop(), then return
    # SequentialBuilder(participants=[agent]).build().
    raise NotImplementedError("build_workflow is not implemented yet")


def build_harness_agent(client) -> Agent:
    """Layer 3: a harness agent, with file access and approval gating built in."""
    # TODO(lab-21): return create_harness_agent(client, ...) with a name,
    # agent_instructions, tools=[suggest_gear_for_trail], and
    # disable_web_search=True (this client doesn't support web search).
    raise NotImplementedError("build_harness_agent is not implemented yet")


def main() -> None:
    import asyncio
    import os

    from agent_framework.foundry import FoundryChatClient

    client = FoundryChatClient(
        project_endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"],
        model=os.environ.get("LOW_COST_DEPLOYMENT", "cascadia-low-cost"),
    )

    loop_agent = build_agent_loop(client)
    loop_response = asyncio.run(loop_agent.run("Plan gear for the Cascade Pass Loop."))
    print(f"Agent loop: {loop_response.text}")

    workflow = build_workflow(client)
    workflow_result = asyncio.run(workflow.run("Plan gear for the Cascade Pass Loop."))
    print(f"Workflow: {workflow_result}")

    harness_agent = build_harness_agent(client)
    harness_response = asyncio.run(harness_agent.run("Plan gear for the Cascade Pass Loop."))
    print(f"Harness: {harness_response.text}")


if __name__ == "__main__":
    main()
