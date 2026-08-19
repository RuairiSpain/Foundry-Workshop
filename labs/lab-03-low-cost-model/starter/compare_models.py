"""Compares the attendee's own low-cost deployment against the hub's
shared router, on the same prompt.
"""

from __future__ import annotations

import dataclasses


@dataclasses.dataclass
class ModelReply:
    deployment_name: str
    content: str
    total_tokens: int


@dataclasses.dataclass
class ComparisonResult:
    low_cost: ModelReply
    router: ModelReply

    @property
    def token_difference(self) -> int:
        """Positive when the router used more tokens than the low-cost model."""
        return self.router.total_tokens - self.low_cost.total_tokens


def _call_model(chat_client, *, deployment_name: str, prompt: str) -> ModelReply:
    # TODO(lab-03): call chat_client.complete() with `model=deployment_name`
    # and a one-message conversation containing `prompt`.
    #
    # TODO(lab-03): build and return a ModelReply from the response —
    # response.choices[0].message.content and response.usage.total_tokens.
    raise NotImplementedError("_call_model is not implemented yet")


def run_comparison(client, prompt: str, *, low_cost_deployment: str, router_deployment: str) -> ComparisonResult:
    """Sends the same prompt to both deployments and returns both replies."""
    # TODO(lab-03): get a chat completions client from client.inference,
    # call _call_model() once per deployment, and return a
    # ComparisonResult.
    raise NotImplementedError("run_comparison is not implemented yet")


def main() -> None:
    import os

    from azure.ai.projects import AIProjectClient
    from azure.identity import DefaultAzureCredential

    endpoint = os.environ["FOUNDRY_PROJECT_ENDPOINT"]
    client = AIProjectClient(endpoint=endpoint, credential=DefaultAzureCredential())
    result = run_comparison(
        client,
        "In one sentence, what does Cascadia Outfitters sell?",
        low_cost_deployment=os.environ.get("LOW_COST_DEPLOYMENT", "cascadia-low-cost"),
        router_deployment=os.environ.get("ROUTER_DEPLOYMENT", "cascadia-router"),
    )
    print(f"Low-cost ({result.low_cost.total_tokens} tokens): {result.low_cost.content}")
    print(f"Router ({result.router.total_tokens} tokens): {result.router.content}")
    print(f"Token difference: {result.token_difference}")


if __name__ == "__main__":
    main()
