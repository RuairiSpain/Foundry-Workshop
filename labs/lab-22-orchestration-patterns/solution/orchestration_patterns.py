"""Builds the same Cascadia specialist scenario four ways with
`agent_framework.orchestrations`: sequential, concurrent, handoff, and
Magentic — landing on Magentic as the pattern for the full scenario,
where an open-ended manager plans and delegates instead of following a
fixed shape.
"""

from __future__ import annotations

from agent_framework import Agent
from agent_framework.orchestrations import ConcurrentBuilder, HandoffBuilder, MagenticBuilder, SequentialBuilder


def build_triage_agent(client) -> Agent:
    return Agent(client, name="triage", instructions="Classify the customer's request and summarize it.")


def build_order_agent(client) -> Agent:
    return Agent(client, name="order", instructions="Answer order-status questions.")


def build_trip_planner_agent(client) -> Agent:
    return Agent(client, name="trip-planner", instructions="Recommend gear and routes for hikes.")


def build_innovation_agent(client) -> Agent:
    return Agent(
        client,
        name="innovation",
        instructions=(
            "Propose one trail-bundle promotion idea combining a product and a trail, "
            "based on what the other participants discussed."
        ),
    )


def build_manager_agent(client) -> Agent:
    """The Magentic manager: plans, delegates, and decides when the task
    is done. Separate from the specialist agents on purpose — Magentic
    requires an explicit manager, unlike Sequential or Concurrent, which
    just run whichever participants you give them.
    """
    return Agent(client, name="manager", instructions="Coordinate the specialists and produce a final answer.")


def build_sequential_workflow(client):
    """Triage, then order — each participant sees the previous one's
    output, in a fixed order. Use this when step order matters.
    """
    triage = build_triage_agent(client)
    order = build_order_agent(client)
    return SequentialBuilder(participants=[triage, order]).build()


def build_concurrent_workflow(client):
    """Order and trip-planner run on the same input at once, fanning in
    to one result. Use this when two specialists don't depend on each
    other's output — unlike Sequential, where order matters.
    """
    order = build_order_agent(client)
    trip_planner = build_trip_planner_agent(client)
    return ConcurrentBuilder(participants=[order, trip_planner]).build()


def build_handoff_workflow(client):
    """Triage starts the conversation and can hand off to order —
    control transfers between agents instead of every agent seeing every
    turn. Handoff participants must opt in to
    `require_per_service_call_history_persistence`, since handoffs can
    short-circuit a tool call mid-flight and the local history has to
    stay consistent with the service when that happens.
    """
    triage = Agent(
        client,
        name="triage",
        instructions="Classify requests.",
        require_per_service_call_history_persistence=True,
    )
    order = Agent(
        client,
        name="order",
        instructions="Answer order-status questions.",
        require_per_service_call_history_persistence=True,
    )
    return HandoffBuilder(participants=[triage, order]).with_start_agent(triage).add_handoff(triage, [order]).build()


def build_magentic_workflow(client):
    """The full scenario: a manager plans and delegates across triage,
    order, trip-planner, and innovation — an open-ended loop, not a
    fixed sequence or a fixed fan-out. This is the pattern the rest of
    the workshop's multi-agent scenario builds on.
    """
    manager = build_manager_agent(client)
    participants = [
        build_triage_agent(client),
        build_order_agent(client),
        build_trip_planner_agent(client),
        build_innovation_agent(client),
    ]
    return MagenticBuilder(participants=participants, manager_agent=manager).build()


def main() -> None:  # pragma: no cover - real SDK wiring, live model calls, and a CLI entry point, exercised manually
    import asyncio
    import os

    from agent_framework.foundry import FoundryChatClient
    from azure.identity import DefaultAzureCredential

    client = FoundryChatClient(
        project_endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"],
        model=os.environ.get("ROUTER_DEPLOYMENT", "cascadia-router"),
        credential=DefaultAzureCredential(),
    )

    magentic_workflow = build_magentic_workflow(client)
    result = asyncio.run(
        magentic_workflow.run(
            "Maya asks: I loved my last order, what trail and gear bundle would you promote to hikers like me?"
        )
    )
    # result is a WorkflowRunResult — a list of every event the run
    # emitted (agent handoffs, tool calls, status changes), not just the
    # final answer. get_outputs() filters down to what the workflow
    # actually produced.
    for output in result.get_outputs():
        print(output)


if __name__ == "__main__":  # pragma: no cover
    main()
