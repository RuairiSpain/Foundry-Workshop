"""Sends a batch of triage questions through the hub's model router and
records which underlying model handled each one.

Model router picks a different underlying model per turn based on the
prompt's complexity — an easy FAQ question might route to a cheap model,
while a multi-item policy question routes to a stronger one. The
deployment you call is always "cascadia-router"; the response tells you
which underlying model actually answered.
"""

from __future__ import annotations

import dataclasses


@dataclasses.dataclass
class RoutedReply:
    question: str
    underlying_model: str
    content: str


def triage_questions() -> list[str]:
    """Cascadia's fixture triage questions, deliberately mixed in difficulty."""
    return [
        "What is your return window?",
        (
            "I bought a tent and a pair of boots on the same order last month. "
            "The tent has a broken pole and the boots have a worn sole after "
            "three short hikes. What happens if I only want to return one item "
            "and keep the other, and does the worn-gear guarantee change the answer?"
        ),
        "Are store hours the same on weekends?",
    ]


def route_question(chat_client, question: str, *, router_deployment: str) -> RoutedReply:
    response = chat_client.chat.completions.create(
        model=router_deployment,
        messages=[{"role": "user", "content": question}],
    )
    return RoutedReply(
        question=question,
        underlying_model=response.model,
        content=response.choices[0].message.content,
    )


def route_all(client, questions: list[str], *, router_deployment: str) -> list[RoutedReply]:
    """Routes every question and returns one RoutedReply per question, in order."""
    chat_client = client.get_openai_client()
    return [route_question(chat_client, question, router_deployment=router_deployment) for question in questions]


def summarize_routing(replies: list[RoutedReply]) -> dict[str, int]:
    """Counts how many questions each underlying model handled.

    Reading this summary is the point of the lab: if every question
    routes to the same model, the router isn't behaving dynamically for
    this batch, and it's worth checking the trace to see why.
    """
    counts: dict[str, int] = {}
    for reply in replies:
        counts[reply.underlying_model] = counts.get(reply.underlying_model, 0) + 1
    return counts


def main() -> None:  # pragma: no cover - real SDK wiring and CLI entry point, exercised manually
    import os

    from azure.ai.projects import AIProjectClient
    from azure.identity import DefaultAzureCredential

    endpoint = os.environ["FOUNDRY_PROJECT_ENDPOINT"]
    client = AIProjectClient(endpoint=endpoint, credential=DefaultAzureCredential())
    router_deployment = os.environ.get("ROUTER_DEPLOYMENT", "cascadia-router")
    replies = route_all(client, triage_questions(), router_deployment=router_deployment)
    for reply in replies:
        print(f"[{reply.underlying_model}] {reply.question[:60]}...")
    print(summarize_routing(replies))


if __name__ == "__main__":  # pragma: no cover
    main()
