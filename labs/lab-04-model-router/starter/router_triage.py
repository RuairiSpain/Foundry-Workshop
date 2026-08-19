"""Sends a batch of triage questions through the hub's model router and
records which underlying model handled each one.
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
    # TODO(lab-04): call chat_client.complete() with `model=router_deployment`
    # and a one-message conversation containing `question`.
    #
    # TODO(lab-04): build and return a RoutedReply. The underlying model
    # that answered is on `response.model` — it can differ from
    # `router_deployment`, which is the name you called.
    raise NotImplementedError("route_question is not implemented yet")


def route_all(client, questions: list[str], *, router_deployment: str) -> list[RoutedReply]:
    """Routes every question and returns one RoutedReply per question, in order."""
    # TODO(lab-04): get a chat completions client from client.inference,
    # then call route_question() once per question.
    raise NotImplementedError("route_all is not implemented yet")


def summarize_routing(replies: list[RoutedReply]) -> dict[str, int]:
    """Counts how many questions each underlying model handled."""
    # TODO(lab-04): return a dict mapping underlying_model -> count.
    raise NotImplementedError("summarize_routing is not implemented yet")


def main() -> None:
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


if __name__ == "__main__":
    main()
