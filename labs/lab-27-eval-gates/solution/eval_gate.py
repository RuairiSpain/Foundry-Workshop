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
    if not must_contain:
        return 1.0
    reply_lower = reply.lower()
    hits = sum(1 for phrase in must_contain if phrase.lower() in reply_lower)
    return hits / len(must_contain)


def evaluate_deployment(chat_client, *, deployment_name: str, dataset: list[dict] = EVAL_DATASET) -> float:
    """Runs the eval dataset against one deployment and returns the average score."""
    scores = []
    for item in dataset:
        response = chat_client.chat.completions.create(
            model=deployment_name, messages=[{"role": "user", "content": item["question"]}]
        )
        scores.append(score_reply(response.choices[0].message.content, must_contain=item["must_contain"]))
    return sum(scores) / len(scores)


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
    baseline_score = evaluate_deployment(chat_client, deployment_name=baseline_deployment, dataset=dataset)
    candidate_score = evaluate_deployment(chat_client, deployment_name=candidate_deployment, dataset=dataset)
    return GateResult(
        baseline_score=baseline_score, candidate_score=candidate_score, max_allowed_regression=max_allowed_regression
    )


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
    """Runs the gate; only publishes and canaries the new version if it passes.

    Raises RegressionError instead of publishing a version nobody
    approved traffic for — a caller has to catch this and decide what
    to do next, rather than a silent skip going unnoticed in a pipeline.
    """
    gate_result = run_evaluation_gate(
        chat_client,
        baseline_deployment=baseline_deployment,
        candidate_deployment=candidate_deployment,
        max_allowed_regression=max_allowed_regression,
    )
    if not gate_result.passed:
        raise RegressionError(
            f"Candidate scored {gate_result.candidate_score:.2f}, baseline scored "
            f"{gate_result.baseline_score:.2f}. Regression exceeds the allowed "
            f"{gate_result.max_allowed_regression:.2f}."
        )
    version = agent_applications_client.publish_version(app_id, agent_id=agent_id, notes=notes)
    agent_applications_client.set_traffic_split(app_id, {stable_version: 90.0, version.version: 10.0})
    return version


def main() -> None:  # pragma: no cover - real SDK wiring and CLI entry point, exercised manually
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


if __name__ == "__main__":  # pragma: no cover
    main()
