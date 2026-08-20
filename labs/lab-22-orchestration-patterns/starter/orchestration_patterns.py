"""Builds the same Cascadia specialist scenario four ways with
`agent_framework.orchestrations`: sequential, concurrent, handoff, and
Magentic.
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
    """The Magentic manager: plans, delegates, and decides when the task is done."""
    return Agent(client, name="manager", instructions="Coordinate the specialists and produce a final answer.")


def build_sequential_workflow(client):
    """Triage, then order — each participant sees the previous one's output, in order."""
    # TODO(lab-22): build a triage and an order agent, and return
    # SequentialBuilder(participants=[triage, order]).build().
    raise NotImplementedError("build_sequential_workflow is not implemented yet")


def build_concurrent_workflow(client):
    """Order and trip-planner run on the same input at once, fanning in to one result."""
    # TODO(lab-22): build an order and a trip-planner agent, and return
    # ConcurrentBuilder(participants=[order, trip_planner]).build().
    raise NotImplementedError("build_concurrent_workflow is not implemented yet")


def build_handoff_workflow(client):
    """Triage starts the conversation and can hand off to order."""
    # TODO(lab-22): build a triage and an order Agent, each with
    # require_per_service_call_history_persistence=True. Return
    # HandoffBuilder(participants=[triage, order])
    #   .with_start_agent(triage)
    #   .add_handoff(triage, [order])
    #   .build()
    raise NotImplementedError("build_handoff_workflow is not implemented yet")


def build_magentic_workflow(client):
    """The full scenario: a manager plans and delegates across triage,
    order, trip-planner, and innovation.
    """
    # TODO(lab-22): build a manager agent and the four specialist
    # agents, and return
    # MagenticBuilder(participants=[...], manager_agent=manager).build().
    raise NotImplementedError("build_magentic_workflow is not implemented yet")


def main() -> None:
    import asyncio
    import os

    from agent_framework.foundry import FoundryChatClient

    client = FoundryChatClient(
        project_endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"],
        model=os.environ.get("ROUTER_DEPLOYMENT", "cascadia-router"),
    )

    magentic_workflow = build_magentic_workflow(client)
    result = asyncio.run(
        magentic_workflow.run(
            "Maya asks: I loved my last order, what trail and gear bundle would you promote to hikers like me?"
        )
    )
    print(result)


if __name__ == "__main__":
    main()
