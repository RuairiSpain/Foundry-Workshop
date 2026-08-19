"""Compares the attendee's own low-cost deployment against the hub's
shared router, on the same prompt.

This is the Playground's "View Code" step made real: the compare view
runs the same two calls in the UI. This exact call shape — get a chat
completions client, call complete() with a deployment name — reappears
in Lab 04's router and Lab 05's tuning.
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
    response = chat_client.complete(
        model=deployment_name,
        messages=[{"role": "user", "content": prompt}],
    )
    return ModelReply(
        deployment_name=deployment_name,
        content=response.choices[0].message.content,
        total_tokens=response.usage.total_tokens,
    )


def run_comparison(client, prompt: str, *, low_cost_deployment: str, router_deployment: str) -> ComparisonResult:
    """Sends the same prompt to both deployments and returns both replies."""
    chat_client = client.inference.get_chat_completions_client()
    low_cost = _call_model(chat_client, deployment_name=low_cost_deployment, prompt=prompt)
    router = _call_model(chat_client, deployment_name=router_deployment, prompt=prompt)
    return ComparisonResult(low_cost=low_cost, router=router)


def main() -> None:  # pragma: no cover - real SDK wiring and CLI entry point, exercised manually
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


if __name__ == "__main__":  # pragma: no cover
    main()
