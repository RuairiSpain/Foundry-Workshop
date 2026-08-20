"""The capstone: composes the workshop's full multi-agent scenario into
one operated system.

`build_governed_workflow()` assembles the Magentic fleet Lab 22
introduced, now including Lab 23's store-ops specialist when it's
available. The rest of this module doesn't re-derive the checks Labs
27, 29, 30, and 32 each introduced separately — it takes their
*results* as input and makes one release decision from all of them at
once, the way a real release process consults evaluation, safety,
network, and governance findings together rather than one at a time.
"""

from __future__ import annotations

import dataclasses

from agent_framework import Agent
from agent_framework.orchestrations import MagenticBuilder


def build_governed_workflow(client, *, include_store_ops: bool = False):
    """Builds the Magentic workflow for the full Cascadia scenario.

    Always includes the manager and the four specialists Lab 22
    introduced. Adds Lab 23's `GitHubCopilotAgent`-backed store-ops
    specialist only when `include_store_ops` is True — the same
    license-gated opt-in Lab 23's README asked you to make for
    yourself, generalized here to the whole fleet.
    """
    manager = Agent(client, name="manager", instructions="Coordinate every specialist and produce a final answer.")
    participants: list = [
        Agent(client, name="triage", instructions="Classify the customer's request and summarize it."),
        Agent(client, name="order", instructions="Answer order-status questions."),
        Agent(
            client,
            name="trip-planner",
            instructions="Recommend gear and routes for hikes, delegating shipping ETAs to SwiftShip.",
        ),
        Agent(
            client,
            name="innovation",
            instructions="Propose one trail-bundle promotion idea based on what the other specialists discussed.",
        ),
    ]
    if include_store_ops:
        from agent_framework.github import GitHubCopilotAgent

        participants.append(
            GitHubCopilotAgent(
                "You edit Cascadia store-ops config files. Propose changes; never write one directly. "
                "A human approves every change before it's applied.",
                name="store-ops",
            )
        )
    return MagenticBuilder(participants=participants, manager_agent=manager).build()


@dataclasses.dataclass
class FleetComponent:
    name: str
    lab: str
    optional: bool = False


def build_fleet_manifest(*, include_store_ops: bool = False, include_teams_channel: bool = False) -> list[FleetComponent]:
    """Declares every component the full ecosystem can include, honoring
    which license-gated optional pieces (Labs 23 and 31) this attendee
    actually has access to. Lab 25's SwiftShip hop and Lab 30's gateway
    aren't separate fleet components — they're how trip-planner and
    every specialist are reached, not specialists themselves.
    """
    components = [
        FleetComponent(name="manager", lab="22"),
        FleetComponent(name="triage", lab="22"),
        FleetComponent(name="order", lab="22"),
        FleetComponent(name="trip-planner", lab="22, 25"),
        FleetComponent(name="innovation", lab="22"),
    ]
    if include_store_ops:
        components.append(FleetComponent(name="store-ops", lab="23", optional=True))
    if include_teams_channel:
        components.append(FleetComponent(name="teams-channel", lab="31", optional=True))
    return components


@dataclasses.dataclass
class ReleaseGateResult:
    cleared: bool
    blocking_reasons: list[str]


def evaluate_release_gates(
    *,
    eval_score: float,
    eval_threshold: float,
    content_safety_violations: list[str],
    network_problems: list[str],
    governance_violations: list[str],
) -> ReleaseGateResult:
    """Combines Lab 27's eval gate, Lab 29's Content Safety policy,
    Lab 30's network validation, and Lab 32's governance policy into
    one release decision.

    Collects every blocking reason instead of stopping at the first —
    an operator fixing a release should see the whole list in one pass,
    the same principle Lab 32's `evaluate_governance_policy()` already
    applied to one policy; this applies it across all four.
    """
    reasons: list[str] = []
    if eval_score < eval_threshold:
        reasons.append(f"Evaluation score {eval_score} is below the required threshold {eval_threshold}")
    reasons.extend(f"Content Safety: {violation}" for violation in content_safety_violations)
    reasons.extend(f"Network: {problem}" for problem in network_problems)
    reasons.extend(f"Governance: {violation}" for violation in governance_violations)
    return ReleaseGateResult(cleared=not reasons, blocking_reasons=reasons)


def summarize_release_readiness(gate_result: ReleaseGateResult, fleet: list[FleetComponent]) -> str:
    """Builds the one-line-per-issue summary an operator reads before
    deciding whether to publish a new version (Lab 26) of the fleet.
    """
    component_names = ", ".join(component.name for component in fleet)
    if gate_result.cleared:
        return f"CLEARED to release. Fleet: {component_names}."
    reasons = "\n".join(f"  - {reason}" for reason in gate_result.blocking_reasons)
    return f"BLOCKED. Fleet: {component_names}.\n{reasons}"


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
    include_store_ops = os.environ.get("HAS_GITHUB_COPILOT_SDK", "false").lower() == "true"
    workflow = build_governed_workflow(client, include_store_ops=include_store_ops)
    fleet = build_fleet_manifest(include_store_ops=include_store_ops)

    gate_result = evaluate_release_gates(
        eval_score=float(os.environ.get("EVAL_SCORE", "0.9")),
        eval_threshold=0.8,
        content_safety_violations=[],
        network_problems=[],
        governance_violations=[],
    )
    print(summarize_release_readiness(gate_result, fleet))
    if not gate_result.cleared:
        return

    result = asyncio.run(
        workflow.run("Maya asks: I loved my last order, what trail and gear bundle would you promote to hikers like me?")
    )
    # result is a WorkflowRunResult — a list of every event the run
    # emitted, not just the final answer. get_outputs() filters down to
    # what the workflow actually produced.
    for output in result.get_outputs():
        print(output)


if __name__ == "__main__":  # pragma: no cover
    main()
