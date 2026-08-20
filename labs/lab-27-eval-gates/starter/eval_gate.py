"""Wires Lab 15's batch evaluation into a release gate: a new agent
version only gets traffic if it doesn't regress against the currently
live version.

Agent Applications have no stable typed SDK as of writing this
workshop — a real call goes through `AIProjectClient.send_request()`
against a preview REST surface. `agent_applications_client` below is
this lab's own stand-in for that surface. See main() for the caveat
spelled out inline.
"""

from __future__ import annotations

import dataclasses

EVAL_DATASET: list[dict] = [
    {"question": "What is your return window?", "must_contain": ["60 days"]},
    {"question": "Can I return a carabiner I already opened?", "must_contain": ["non-returnable"]},
]


class RegressionError(RuntimeError):
    """Raised when a candidate version's score doesn't clear the gate."""


def score_reply(reply: str, *, must_contain: list[str]) -> float:
    """Fraction of required phrases found in `reply`, case-insensitively."""
    # TODO(lab-27): same logic as Lab 14/15's scoring functions.
    raise NotImplementedError("score_reply is not implemented yet")


def evaluate_deployment(chat_client, *, deployment_name: str, dataset: list[dict] = EVAL_DATASET) -> float:
    """Runs the eval dataset against one deployment and returns the average score."""
    # TODO(lab-27): call chat_client.chat.completions.create() once per dataset item,
    # score each reply with score_reply(), and return the average.
    raise NotImplementedError("evaluate_deployment is not implemented yet")


@dataclasses.dataclass
class GateResult:
    baseline_score: float
    candidate_score: float
    max_allowed_regression: float

    @property
    def passed(self) -> bool:
        return self.candidate_score >= self.baseline_score - self.max_allowed_regression


def run_evaluation_gate(
    chat_client,
    *,
    baseline_deployment: str,
    candidate_deployment: str,
    max_allowed_regression: float = 0.1,
    dataset: list[dict] = EVAL_DATASET,
) -> GateResult:
    """Scores both deployments and decides whether the candidate clears the gate."""
    # TODO(lab-27): call evaluate_deployment() for both baseline_deployment
    # and candidate_deployment, and return a GateResult.
    raise NotImplementedError("run_evaluation_gate is not implemented yet")


def publish_if_gate_passes(
    agent_applications_client,
    chat_client,
    app_id: str,
    *,
    agent_id: str,
    baseline_deployment: str,
    candidate_deployment: str,
    stable_version: int,
    notes: str,
    max_allowed_regression: float = 0.1,
):
    """Runs the gate; only publishes and canaries the new version if it passes."""
    # TODO(lab-27): call run_evaluation_gate(). If it doesn't pass, raise
    # RegressionError with the scores in the message. Otherwise call
    # agent_applications_client.publish_version(), then
    # set_traffic_split() giving the new version 10% and stable_version
    # 90%, and return the new version.
    raise NotImplementedError("publish_if_gate_passes is not implemented yet")


def main() -> None:
    import os

    from azure.ai.projects import AIProjectClient
    from azure.identity import DefaultAzureCredential

    endpoint = os.environ["FOUNDRY_PROJECT_ENDPOINT"]
    # client.agent_applications is this lab's own stand-in — Agent
    # Applications have no stable typed SDK yet, so a real call goes
    # through client.send_request() against a preview REST surface.
    client = AIProjectClient(endpoint=endpoint, credential=DefaultAzureCredential(), allow_preview=True)

    version = publish_if_gate_passes(
        client.agent_applications,
        client.get_openai_client(),
        os.environ["AGENT_APPLICATION_ID"],
        agent_id=os.environ["CANDIDATE_AGENT_ID"],
        baseline_deployment=os.environ.get("LOW_COST_DEPLOYMENT", "cascadia-low-cost"),
        candidate_deployment=os.environ["CANDIDATE_DEPLOYMENT"],
        stable_version=int(os.environ.get("STABLE_VERSION", "1")),
        notes="Automated release, gated on evaluation.",
    )
    print(f"Published and canaried version {version.version}.")


if __name__ == "__main__":
    main()
