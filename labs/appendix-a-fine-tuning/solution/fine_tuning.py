"""Fine-tunes a deployed model on Cascadia-specific examples, then
compares it against the shared router baseline (Lab 03's comparison
pattern) on the same evaluation dataset shape Lab 15 introduced.

Foundry's fine-tuning API was still in preview as of writing this
workshop, so this module isn't verified against a stable public SDK the
way most other labs are — `case-study/testing/foundry_mocks.py`'s
`FakeFineTuningClient` models the shape every fine-tuning API in this
family shares (submit against a training file, poll until done, get
back a deployable model name), not one confirmed surface.
"""

from __future__ import annotations

import dataclasses
import time


def build_fine_tuning_dataset(examples: list[dict]) -> list[dict]:
    """Converts `{"question": ..., "answer": ...}` pairs into the chat
    fine-tuning record shape a training file upload expects.
    """
    return [
        {
            "messages": [
                {"role": "user", "content": example["question"]},
                {"role": "assistant", "content": example["answer"]},
            ]
        }
        for example in examples
    ]


class FineTuningJobFailedError(RuntimeError):
    """Raised when a fine-tuning job's terminal status is 'failed'."""


def submit_fine_tuning_job(fine_tuning_client, *, base_model: str, training_file_id: str, suffix: str):
    """Submits a fine-tuning job against an already-uploaded training file."""
    return fine_tuning_client.create(base_model=base_model, training_file_id=training_file_id, suffix=suffix)


def poll_until_complete(fine_tuning_client, job_id: str, *, max_polls: int = 10, poll_interval_seconds: float = 0.0):
    """Polls a fine-tuning job until it succeeds or fails.

    Raises `FineTuningJobFailedError` on a 'failed' status, and
    `TimeoutError` if the job hasn't reached a terminal status within
    `max_polls` — a job that never finishes should fail loudly here
    instead of hanging a caller forever. `poll_interval_seconds`
    defaults to 0 so tests don't sleep; production code passes a real
    interval.
    """
    for _ in range(max_polls):
        job = fine_tuning_client.get(job_id)
        if job.status == "succeeded":
            return job
        if job.status == "failed":
            raise FineTuningJobFailedError(f"Fine-tuning job {job_id} failed")
        if poll_interval_seconds:
            time.sleep(poll_interval_seconds)
    raise TimeoutError(f"Fine-tuning job {job_id} did not complete after {max_polls} polls")


def score_groundedness(reply: str, *, must_contain: list[str]) -> float:
    """Fraction of required phrases found in `reply`, case-insensitively.

    The same scoring approach Lab 15 used for the base router — reused
    here as the one fair yardstick for comparing the fine-tuned model
    against it.
    """
    if not must_contain:
        return 1.0
    reply_lower = reply.lower()
    hits = sum(1 for phrase in must_contain if phrase.lower() in reply_lower)
    return hits / len(must_contain)


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
    reply's groundedness, so the fine-tuned model is judged on the same
    dataset and the same yardstick as the router it's meant to beat.
    """
    results = []
    for item in dataset:
        fine_tuned_response = chat_client.complete(
            model=fine_tuned_deployment, messages=[{"role": "user", "content": item["question"]}]
        )
        router_response = chat_client.complete(
            model=router_deployment, messages=[{"role": "user", "content": item["question"]}]
        )
        fine_tuned_reply = fine_tuned_response.choices[0].message.content
        router_reply = router_response.choices[0].message.content
        results.append(
            BaselineComparison(
                question=item["question"],
                fine_tuned_reply=fine_tuned_reply,
                router_reply=router_reply,
                fine_tuned_groundedness=score_groundedness(fine_tuned_reply, must_contain=item["must_contain"]),
                router_groundedness=score_groundedness(router_reply, must_contain=item["must_contain"]),
            )
        )
    return results


def summarize_comparison(results: list[BaselineComparison]) -> dict[str, int]:
    """Counts wins, losses, and ties across every comparison — the
    one-line verdict on whether fine-tuning was worth it.
    """
    fine_tuned_wins = sum(1 for result in results if result.fine_tuned_groundedness > result.router_groundedness)
    router_wins = sum(1 for result in results if result.router_groundedness > result.fine_tuned_groundedness)
    ties = len(results) - fine_tuned_wins - router_wins
    return {"fine_tuned_wins": fine_tuned_wins, "router_wins": router_wins, "ties": ties}


def main() -> None:  # pragma: no cover - real SDK wiring and CLI entry point, exercised manually
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
    training_file = client.files.upload(file_path="cascadia-return-policy-examples.jsonl")
    job = submit_fine_tuning_job(
        client.fine_tuning,
        base_model=os.environ.get("LOW_COST_DEPLOYMENT", "cascadia-low-cost"),
        training_file_id=training_file.id,
        suffix="cascadia-returns",
    )
    completed_job = poll_until_complete(client.fine_tuning, job.id, poll_interval_seconds=30)
    print(f"Fine-tuned model ready: {completed_job.fine_tuned_model}")

    eval_dataset = [
        {"question": "What is your return window?", "must_contain": ["60 days"]},
        {"question": "Can I return a carabiner I already opened?", "must_contain": ["non-returnable"]},
    ]
    chat_client = client.inference.get_chat_completions_client()
    results = compare_against_baseline(
        chat_client,
        eval_dataset,
        fine_tuned_deployment=completed_job.fine_tuned_model,
        router_deployment=os.environ.get("ROUTER_DEPLOYMENT", "cascadia-router"),
    )
    print(summarize_comparison(results))


if __name__ == "__main__":  # pragma: no cover
    main()
