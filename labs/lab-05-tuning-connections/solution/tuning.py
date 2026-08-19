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
    """Assembles the keyword arguments for chat_client.complete().

    A separate function so a test can check the exact parameter set
    without also making a call. `seed` is omitted unless given — passing
    `seed=None` explicitly to some Foundry models is rejected outright,
    rather than treated as "no seed."
    """
    kwargs: dict = {"temperature": temperature, "top_p": top_p, "max_tokens": max_tokens}
    if seed is not None:
        kwargs["seed"] = seed
    return kwargs


def call_with_params(chat_client, prompt: str, *, deployment_name: str, **params) -> TunedReply:
    """Sends one prompt with the given inference parameters."""
    kwargs = build_completion_kwargs(**params)
    response = chat_client.complete(
        model=deployment_name,
        messages=[{"role": "user", "content": prompt}],
        **kwargs,
    )
    return TunedReply(
        content=response.choices[0].message.content,
        total_tokens=response.usage.total_tokens,
        cached_tokens=response.usage.cached_tokens,
    )


def sweep_temperature(chat_client, prompt: str, *, deployment_name: str, temperatures: list[float]) -> list[TunedReply]:
    """Calls the same prompt once per temperature value, in order."""
    return [
        call_with_params(chat_client, prompt, deployment_name=deployment_name, temperature=temperature)
        for temperature in temperatures
    ]


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

    A cache hit shows up as `usage.cached_tokens > 0` on the second
    call. The first call is expected to miss, since there's nothing to
    cache yet.
    """
    first = call_with_params(chat_client, prompt, deployment_name=deployment_name)
    second = call_with_params(chat_client, prompt, deployment_name=deployment_name)
    return CacheReport(first_call_cached_tokens=first.cached_tokens, second_call_cached_tokens=second.cached_tokens)


def main() -> None:  # pragma: no cover - real SDK wiring and CLI entry point, exercised manually
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


if __name__ == "__main__":  # pragma: no cover
    main()
