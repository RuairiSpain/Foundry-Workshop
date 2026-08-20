"""Introduces Microsoft Agent Framework's three layers — agent loop,
workflow, harness — by building Lab 12's Trip Planner all three ways: as
a plain agent, wrapped in a one-node workflow, and as a harness agent
with file access and approval gating built in.
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
    """Layer 1: the agent loop. One agent, one reasoning/act cycle per
    call to `.run()` — this is exactly Lab 12's Agent, unchanged.
    """
    return Agent(
        client,
        name="cascadia-trip-planner",
        instructions="You help Cascadia customers plan hikes using suggest_gear_for_trail.",
        tools=[suggest_gear_for_trail],
    )


def build_workflow(client):
    """Layer 2: a workflow. A one-participant SequentialBuilder is the
    simplest possible workflow — the same agent loop from layer 1,
    wrapped so it can be composed with other agents later. Lab 22 is
    where a workflow's value actually shows up: multiple participants.
    """
    agent = build_agent_loop(client)
    return SequentialBuilder(participants=[agent]).build()


def build_harness_agent(client) -> Agent:
    """Layer 3: a harness. Adds capabilities a plain agent loop doesn't
    have — file access with approval gating, a todo tracker,
    context-window compaction for long sessions — configured here
    instead of hand-built as extra tools the way Lab 16's sandbox was.
    """
    return create_harness_agent(
        client,
        name="cascadia-trip-planner-harness",
        agent_instructions="You help Cascadia customers plan hikes using suggest_gear_for_trail.",
        tools=[suggest_gear_for_trail],
        disable_web_search=True,
        loop_max_iterations=5,
    )


def main() -> None:  # pragma: no cover - real SDK wiring and CLI entry point, exercised manually
    import asyncio
    import os

    from agent_framework.foundry import FoundryChatClient
    from azure.identity import DefaultAzureCredential

    client = FoundryChatClient(
        project_endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"],
        model=os.environ.get("LOW_COST_DEPLOYMENT", "cascadia-low-cost"),
        credential=DefaultAzureCredential(),
    )

    loop_agent = build_agent_loop(client)
    loop_response = asyncio.run(loop_agent.run("Plan gear for the Cascade Pass Loop."))
    print(f"Agent loop: {loop_response.text}")

    workflow = build_workflow(client)
    workflow_result = asyncio.run(workflow.run("Plan gear for the Cascade Pass Loop."))
    # workflow_result is a WorkflowRunResult — every event the run
    # emitted, not just the final answer. get_outputs() filters down to
    # what the workflow actually produced.
    print(f"Workflow: {workflow_result.get_outputs()}")

    harness_agent = build_harness_agent(client)
    harness_response = asyncio.run(harness_agent.run("Plan gear for the Cascade Pass Loop."))
    print(f"Harness: {harness_response.text}")


if __name__ == "__main__":  # pragma: no cover
    main()
