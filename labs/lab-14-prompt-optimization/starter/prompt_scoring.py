"""Scores a deliberately weak system prompt against the Prompt
Optimizer's rewritten version, on the same set of support questions.
"""

from __future__ import annotations

import dataclasses

WEAK_SYSTEM_PROMPT = "You are a helpful assistant for a store."

EVAL_QUESTIONS: list[dict] = [
    {"question": "What is your return window?", "must_contain": ["60 days"]},
    {"question": "Can I return a carabiner I already opened?", "must_contain": ["non-returnable"]},
    {"question": "Are your weekend store hours the same as weekdays?", "must_contain": ["10am"]},
]


def score_reply(reply: str, *, must_contain: list[str]) -> float:
    """Fraction of required phrases found in `reply`, case-insensitively."""
    # TODO(lab-14): handle the empty must_contain case (return 1.0), then
    # count how many phrases appear in reply.lower() and return
    # hits / len(must_contain).
    raise NotImplementedError("score_reply is not implemented yet")


@dataclasses.dataclass
class PromptScore:
    system_prompt: str
    per_question_scores: list[float]

    @property
    def average_score(self) -> float:
        return sum(self.per_question_scores) / len(self.per_question_scores)


def score_system_prompt(chat_client, system_prompt: str, *, deployment_name: str, questions: list[dict]) -> PromptScore:
    """Scores one system prompt across every eval question."""
    # TODO(lab-14): for each item in questions, call chat_client.complete()
    # with a system message (system_prompt) and a user message
    # (item["question"]), then call score_reply() on the response content.
    # Return a PromptScore with all the per-question scores.
    raise NotImplementedError("score_system_prompt is not implemented yet")


@dataclasses.dataclass
class PromptComparison:
    weak: PromptScore
    optimized: PromptScore

    @property
    def improved(self) -> bool:
        return self.optimized.average_score > self.weak.average_score


def compare_prompts(
    chat_client, *, weak_prompt: str, optimized_prompt: str, deployment_name: str, questions: list[dict]
) -> PromptComparison:
    # TODO(lab-14): call score_system_prompt() for both prompts and
    # return a PromptComparison built from both scores.
    raise NotImplementedError("compare_prompts is not implemented yet")


def main() -> None:
    import os

    from azure.ai.projects import AIProjectClient
    from azure.identity import DefaultAzureCredential

    endpoint = os.environ["FOUNDRY_PROJECT_ENDPOINT"]
    optimized_prompt = os.environ["OPTIMIZED_SYSTEM_PROMPT"]
    client = AIProjectClient(endpoint=endpoint, credential=DefaultAzureCredential())
    chat_client = client.inference.get_chat_completions_client()
    deployment_name = os.environ.get("LOW_COST_DEPLOYMENT", "cascadia-low-cost")

    comparison = compare_prompts(
        chat_client,
        weak_prompt=WEAK_SYSTEM_PROMPT,
        optimized_prompt=optimized_prompt,
        deployment_name=deployment_name,
        questions=EVAL_QUESTIONS,
    )
    print(f"Weak prompt average score:      {comparison.weak.average_score:.2f}")
    print(f"Optimized prompt average score: {comparison.optimized.average_score:.2f}")
    print(f"Improved: {comparison.improved}")


if __name__ == "__main__":
    main()
