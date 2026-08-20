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
    """Fraction of required phrases found in `reply`, case-insensitively.

    A partial-credit fraction rather than pass/fail, since a reply that
    gets 2 of 3 required facts right is a real, visible improvement over
    0 of 3 — pass/fail would hide that.
    """
    if not must_contain:
        return 1.0
    reply_lower = reply.lower()
    hits = sum(1 for phrase in must_contain if phrase.lower() in reply_lower)
    return hits / len(must_contain)


@dataclasses.dataclass
class PromptScore:
    system_prompt: str
    per_question_scores: list[float]

    @property
    def average_score(self) -> float:
        return sum(self.per_question_scores) / len(self.per_question_scores)


def score_system_prompt(chat_client, system_prompt: str, *, deployment_name: str, questions: list[dict]) -> PromptScore:
    """Scores one system prompt across every eval question."""
    scores = []
    for item in questions:
        response = chat_client.complete(
            model=deployment_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": item["question"]},
            ],
        )
        reply = response.choices[0].message.content
        scores.append(score_reply(reply, must_contain=item["must_contain"]))
    return PromptScore(system_prompt=system_prompt, per_question_scores=scores)


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
    weak_score = score_system_prompt(chat_client, weak_prompt, deployment_name=deployment_name, questions=questions)
    optimized_score = score_system_prompt(
        chat_client, optimized_prompt, deployment_name=deployment_name, questions=questions
    )
    return PromptComparison(weak=weak_score, optimized=optimized_score)


def main() -> None:  # pragma: no cover - real SDK wiring and CLI entry point, exercised manually
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


if __name__ == "__main__":  # pragma: no cover
    main()
