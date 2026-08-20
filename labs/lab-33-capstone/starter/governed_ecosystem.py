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

    Build a manager Agent named "manager" and four specialist Agents
    named "triage", "order", "trip-planner", and "innovation" (use
    Lab 22's instructions text as a guide). If `include_store_ops` is
    True, also append a `GitHubCopilotAgent` named "store-ops" (import
    it from `agent_framework.github`). Return
    `MagenticBuilder(participants=..., manager_agent=manager).build()`.
    """
    # TODO: build and return the Magentic workflow.
    raise NotImplementedError


@dataclasses.dataclass
class FleetComponent:
    name: str
    lab: str
    optional: bool = False


def build_fleet_manifest(*, include_store_ops: bool = False, include_teams_channel: bool = False) -> list[FleetComponent]:
    """Declares every component the full ecosystem can include.

    Always include manager, triage, order, trip-planner, and
    innovation. Append a store-ops component (optional=True) if
    `include_store_ops`, and a teams-channel component (optional=True)
    if `include_teams_channel`.
    """
    # TODO: build and return the fleet manifest.
    raise NotImplementedError


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

    Collect every blocking reason (don't stop at the first): if
    `eval_score` is below `eval_threshold`, one reason starting with
    "Evaluation score" (e.g. f"Evaluation score {eval_score} is below
    the required threshold {eval_threshold}"), then one reason per
    content-safety violation (prefixed "Content Safety: "), one per
    network problem (prefixed "Network: "), and one per governance
    violation (prefixed "Governance: "). `cleared` is True only when
    there are no reasons.
    """
    # TODO: build and return the ReleaseGateResult.
    raise NotImplementedError


def summarize_release_readiness(gate_result: ReleaseGateResult, fleet: list[FleetComponent]) -> str:
    """Builds a one-line-per-issue summary an operator reads before
    deciding whether to publish a new version (Lab 26) of the fleet.

    If cleared, return "CLEARED to release. Fleet: <comma-separated
    component names>.". Otherwise return "BLOCKED. Fleet: <names>." on
    the first line, then one "  - <reason>" line per blocking reason.
    """
    # TODO: build and return the summary string.
    raise NotImplementedError


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
