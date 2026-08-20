"""Fine-tunes a deployed model on Cascadia-specific examples, then
compares it against the shared router baseline (Lab 03's comparison
pattern) on the same evaluation dataset shape Lab 15 introduced.

Verified against `openai` 2.54.0's `client.fine_tuning.jobs` — Azure
OpenAI exposes fine-tuning through the same OpenAI-compatible endpoint
Lab 01 onward already uses for chat completions
(`client.get_openai_client()`), not a Foundry-specific one. Whether
fine-tuning is enabled for your project is a capability question for
your instructor, not an SDK-shape one.
"""

from __future__ import annotations

import dataclasses
import time


def build_fine_tuning_dataset(examples: list[dict]) -> list[dict]:
    """Converts `{"question": ..., "answer": ...}` pairs into the chat
    fine-tuning record shape a training file upload expects: a list of
    `{"messages": [{"role": "user", "content": ...}, {"role": "assistant",
    "content": ...}]}` dicts.
    """
    # TODO: build and return the list of training records.
    raise NotImplementedError


class FineTuningJobFailedError(RuntimeError):
    """Raised when a fine-tuning job's terminal status is 'failed'."""


def submit_fine_tuning_job(fine_tuning_jobs_client, *, model: str, training_file: str, suffix: str):
    """Submits a fine-tuning job against an already-uploaded training file.

    Call `fine_tuning_jobs_client.create(...)` with the three keyword
    arguments and return its result.
    """
    # TODO: submit and return the job.
    raise NotImplementedError


def poll_until_complete(fine_tuning_jobs_client, job_id: str, *, max_polls: int = 10, poll_interval_seconds: float = 0.0):
    """Polls a fine-tuning job until it succeeds or fails.

    Call `fine_tuning_jobs_client.retrieve(job_id)` up to `max_polls`
    times. Return the job once its status is "succeeded". Raise
    `FineTuningJobFailedError` on "failed". Sleep `poll_interval_seconds`
    between polls if it's truthy. Raise `TimeoutError` if no terminal
    status was reached within `max_polls`.
    """
    # TODO: implement the poll loop.
    raise NotImplementedError


def score_groundedness(reply: str, *, must_contain: list[str]) -> float:
    """Fraction of required phrases found in `reply`, case-insensitively."""
    # TODO: implement the scoring.
    raise NotImplementedError


@dataclasses.dataclass
class BaselineComparison:
    question: str
    fine_tuned_reply: str
    router_reply: str
    fine_tuned_groundedness: float
    router_groundedness: float

    @property
    def fine_tuned_wins(self) -> bool:
        return self.fine_tuned_groundedness > self.router_groundedness


def compare_against_baseline(
    chat_client, dataset: list[dict], *, fine_tuned_deployment: str, router_deployment: str
) -> list[BaselineComparison]:
    """Runs every eval question against both deployments and scores each
    reply's groundedness with `score_groundedness()`.

    For each item, call `chat_client.chat.completions.create()` once with
    `fine_tuned_deployment` and once with `router_deployment`, in that
    order, and build one `BaselineComparison` per item.
    """
    # TODO: build and return the list of comparisons.
    raise NotImplementedError


def summarize_comparison(results: list[BaselineComparison]) -> dict[str, int]:
    """Counts wins, losses, and ties across every comparison.

    Return {"fine_tuned_wins": ..., "router_wins": ..., "ties": ...}.
    """
    # TODO: build and return the summary dict.
    raise NotImplementedError


def main() -> None:  # pragma: no cover - real SDK wiring and CLI entry point, exercised manually
    import json
    import os

    from azure.ai.projects import AIProjectClient
    from azure.identity import DefaultAzureCredential

    endpoint = os.environ["FOUNDRY_PROJECT_ENDPOINT"]
    client = AIProjectClient(endpoint=endpoint, credential=DefaultAzureCredential())

    examples = [
        {"question": "What is your return window?", "answer": "Cascadia Outfitters accepts returns within 60 days."},
        {
            "question": "Can I return a used carabiner?",
            "answer": "Opened safety gear like carabiners is non-returnable.",
        },
    ]
    dataset_path = "cascadia-return-policy-examples.jsonl"
    with open(dataset_path, "w") as dataset_file:
        for record in build_fine_tuning_dataset(examples):
            dataset_file.write(json.dumps(record) + "\n")

    chat_client = client.get_openai_client()
    with open(dataset_path, "rb") as dataset_file:
        training_file = chat_client.files.create(file=dataset_file, purpose="fine-tune")
    job = submit_fine_tuning_job(
        chat_client.fine_tuning.jobs,
        model=os.environ.get("LOW_COST_DEPLOYMENT", "cascadia-low-cost"),
        training_file=training_file.id,
        suffix="cascadia-returns",
    )
    completed_job = poll_until_complete(chat_client.fine_tuning.jobs, job.id, poll_interval_seconds=30)
    print(f"Fine-tuned model ready: {completed_job.fine_tuned_model}")

    eval_dataset = [
        {"question": "What is your return window?", "must_contain": ["60 days"]},
        {"question": "Can I return a carabiner I already opened?", "must_contain": ["non-returnable"]},
    ]
    results = compare_against_baseline(
        chat_client,
        eval_dataset,
        fine_tuned_deployment=completed_job.fine_tuned_model,
        router_deployment=os.environ.get("ROUTER_DEPLOYMENT", "cascadia-router"),
    )
    print(summarize_comparison(results))


if __name__ == "__main__":  # pragma: no cover
    main()
