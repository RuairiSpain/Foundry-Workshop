"""Tunes inference parameters on a chat completion, and shows what
prompt caching does to token usage on a repeated call.
"""

from __future__ import annotations

import dataclasses


@dataclasses.dataclass
class TunedReply:
    content: str
    total_tokens: int
    cached_tokens: int


def build_completion_kwargs(
    *, temperature: float = 1.0, top_p: float = 1.0, max_tokens: int = 256, seed: int | None = None
) -> dict:
    """Assembles the keyword arguments for chat_client.complete()."""
    # TODO(lab-05): build and return a dict with temperature, top_p, and
    # max_tokens. Include "seed" only when seed is not None.
    raise NotImplementedError("build_completion_kwargs is not implemented yet")


def call_with_params(chat_client, prompt: str, *, deployment_name: str, **params) -> TunedReply:
    """Sends one prompt with the given inference parameters."""
    # TODO(lab-05): build kwargs with build_completion_kwargs(**params),
    # call chat_client.complete() with model, a one-message conversation,
    # and those kwargs, then return a TunedReply.
    raise NotImplementedError("call_with_params is not implemented yet")


def sweep_temperature(chat_client, prompt: str, *, deployment_name: str, temperatures: list[float]) -> list[TunedReply]:
    """Calls the same prompt once per temperature value, in order."""
    # TODO(lab-05): call call_with_params() once per value in temperatures.
    raise NotImplementedError("sweep_temperature is not implemented yet")


@dataclasses.dataclass
class CacheReport:
    first_call_cached_tokens: int
    second_call_cached_tokens: int

    @property
    def cache_hit_on_second_call(self) -> bool:
        return self.second_call_cached_tokens > 0


def check_prompt_caching(chat_client, prompt: str, *, deployment_name: str) -> CacheReport:
    """Sends the same prompt twice and reports whether the second call
    was served from the prompt cache.
    """
    # TODO(lab-05): call call_with_params() twice with the same prompt
    # and deployment_name, and return a CacheReport built from both
    # replies' cached_tokens.
    raise NotImplementedError("check_prompt_caching is not implemented yet")


def main() -> None:
    import os

    from azure.ai.projects import AIProjectClient
    from azure.identity import DefaultAzureCredential

    endpoint = os.environ["FOUNDRY_PROJECT_ENDPOINT"]
    client = AIProjectClient(endpoint=endpoint, credential=DefaultAzureCredential())
    chat_client = client.inference.get_chat_completions_client()
    deployment_name = os.environ.get("LOW_COST_DEPLOYMENT", "cascadia-low-cost")

    prompt = "In one sentence, what does Cascadia Outfitters sell?"

    replies = sweep_temperature(chat_client, prompt, deployment_name=deployment_name, temperatures=[0.0, 0.7, 1.4])
    for temperature, reply in zip([0.0, 0.7, 1.4], replies):
        print(f"temperature={temperature}: {reply.content}")

    report = check_prompt_caching(chat_client, prompt, deployment_name=deployment_name)
    print(f"Cache hit on second call: {report.cache_hit_on_second_call}")


if __name__ == "__main__":
    main()
