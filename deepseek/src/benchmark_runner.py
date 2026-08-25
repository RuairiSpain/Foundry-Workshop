"""Orchestrates one benchmark run: warm-up, the measured work item
list, retries, cooldown, concurrency, resume, dry-run, and writing
output/requests.jsonl (spec 2.6 / 2.7).

Retry policy and the single-attempt HTTP call are deliberately kept in
separate modules (inference_client.py does the attempt; this module
decides whether to retry it) so each can be unit tested independently.
"""

from __future__ import annotations

import dataclasses
import datetime as dt
import json
import random
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Callable, Optional

from .client_factory import ModelClient
from .inference_client import AttemptResult, build_messages, execute_attempt
from .models import (
    BenchmarkSettings,
    ConfigurationError,
    DeploymentResolutionError,
    ModelConfig,
    PricingEntry,
    PromptRecord,
    RequestRecord,
    hash_text,
    redact_record,
)
from .pricing import estimate_cost, select_pricing_entry

DEFAULT_SYSTEM_INSTRUCTION = (
    "You are a helpful, concise assistant for a technical benchmark. Answer the "
    "user's request directly and follow any formatting instructions in it exactly."
)


# ---------------------------------------------------------------------------
# Work items
# ---------------------------------------------------------------------------


@dataclasses.dataclass(frozen=True)
class WorkItem:
    model_logical_name: str
    prompt: PromptRecord
    repeat: int

    @property
    def key(self) -> tuple[str, str, int]:
        return (self.model_logical_name, self.prompt.prompt_id, self.repeat)


def filter_prompts(prompts: list[PromptRecord], settings: BenchmarkSettings) -> list[PromptRecord]:
    filtered = prompts
    if settings.category_filter:
        filtered = [p for p in filtered if p.category == settings.category_filter]
    if settings.difficulty_filter:
        filtered = [p for p in filtered if p.difficulty == settings.difficulty_filter]
    return filtered


def filter_models(model_configs: list[ModelConfig], settings: BenchmarkSettings) -> list[ModelConfig]:
    filtered = [config for config in model_configs if config.enabled]
    if settings.model_filter:
        filtered = [config for config in filtered if config.logical_name == settings.model_filter]
    return filtered


def build_work_items(
    model_configs: list[ModelConfig], prompts: list[PromptRecord], settings: BenchmarkSettings
) -> list[WorkItem]:
    """Builds the full, ordered list of (model, prompt, repeat) work
    items. Model order and prompt order are each independently
    shuffled (or not) using the *same* seeded RNG, so the exact
    ordering is reproducible from `settings.seed` alone. All of one
    model's work items come before the next model's — see the module
    docstring in README.md for why this ordering was chosen over
    interleaving.
    """
    rng = random.Random(settings.seed)
    model_order = [config.logical_name for config in model_configs]
    if settings.randomize_model_order:
        rng.shuffle(model_order)
    prompt_order = list(prompts)
    if settings.randomize_prompt_order:
        rng.shuffle(prompt_order)

    items: list[WorkItem] = []
    for model_name in model_order:
        for prompt in prompt_order:
            for repeat in range(1, settings.repeats + 1):
                items.append(WorkItem(model_logical_name=model_name, prompt=prompt, repeat=repeat))
    return items


# ---------------------------------------------------------------------------
# Dry run
# ---------------------------------------------------------------------------


@dataclasses.dataclass
class DryRunReport:
    run_id: str
    models: list[str]
    total_prompts: int
    repeats: int
    warm_up_per_model: int
    total_work_items: int
    concurrency: int
    streaming: bool
    seed: Optional[int]
    errors: list[str]

    @property
    def is_valid(self) -> bool:
        return not self.errors


def dry_run(model_configs: list[ModelConfig], prompts: list[PromptRecord], settings: BenchmarkSettings) -> DryRunReport:
    """Validates configuration and filters and reports what a real run
    would do — zero network calls.
    """
    errors: list[str] = []
    enabled = [config for config in model_configs if config.enabled]
    if not enabled:
        errors.append("No enabled models in config/models.yaml.")
    if settings.model_filter and settings.model_filter not in {config.logical_name for config in enabled}:
        errors.append(f"model_filter {settings.model_filter!r} does not match any enabled model.")

    filtered_models = filter_models(model_configs, settings)
    filtered_prompts = filter_prompts(prompts, settings)
    if not filtered_prompts:
        errors.append("No prompts match the configured category/difficulty filters.")

    items = build_work_items(filtered_models, filtered_prompts, settings) if not errors else []
    return DryRunReport(
        run_id=settings.run_id,
        models=[config.logical_name for config in filtered_models],
        total_prompts=len(filtered_prompts),
        repeats=settings.repeats,
        warm_up_per_model=settings.warm_up_count,
        total_work_items=len(items),
        concurrency=settings.concurrency,
        streaming=settings.streaming,
        seed=settings.seed,
        errors=errors,
    )


# ---------------------------------------------------------------------------
# Warm-up
# ---------------------------------------------------------------------------


def run_warm_up(model_clients: dict[str, ModelClient], settings: BenchmarkSettings) -> None:
    """Runs `settings.warm_up_count` throwaway requests per model.
    Results are never written anywhere (spec 2.6: "excluded from
    results"). If every warm-up request for a model fails, raises
    DeploymentResolutionError immediately — this is the run's fail-fast
    checkpoint (spec 2.4) before any measured request is attempted.
    """
    if settings.warm_up_count <= 0:
        return
    messages = build_messages(system_instruction=DEFAULT_SYSTEM_INSTRUCTION, user_prompt="Reply with the single word OK.")
    for model_client in model_clients.values():
        failures = 0
        for _ in range(settings.warm_up_count):
            attempt = execute_attempt(
                model_client,
                messages,
                max_output_tokens=16,
                streaming=settings.streaming,
                temperature=settings.temperature,
                top_p=settings.top_p,
                seed=settings.seed,
            )
            if not attempt.succeeded:
                failures += 1
        if failures == settings.warm_up_count:
            raise DeploymentResolutionError(
                logical_name=model_client.config.logical_name,
                deployment_name=model_client.config.deployment_name,
                provider=model_client.config.provider,
                detail=f"all {settings.warm_up_count} warm-up requests failed",
            )


# ---------------------------------------------------------------------------
# Retry / backoff
# ---------------------------------------------------------------------------


def backoff_seconds(attempt_number: int, rng: random.Random, *, base_seconds: float = 1.0, max_seconds: float = 30.0) -> float:
    """Exponential backoff with full jitter: base * 2^(attempt-1), capped,
    plus a random amount up to half the capped backoff.
    """
    backoff = min(max_seconds, base_seconds * (2 ** (attempt_number - 1)))
    return backoff + rng.uniform(0, backoff * 0.5)


def cooldown_seconds(settings: BenchmarkSettings, rng: random.Random) -> float:
    return rng.uniform(settings.cooldown_ms_min / 1000, settings.cooldown_ms_max / 1000)


def execute_with_retries(
    model_client: ModelClient,
    messages: list[dict],
    *,
    max_output_tokens: int,
    settings: BenchmarkSettings,
    rng: random.Random,
    sleep_fn: Callable[[float], None],
) -> tuple[AttemptResult, int]:
    """Calls execute_attempt(), retrying on a retryable failure up to
    `settings.max_retries` times with exponential backoff + jitter.
    Returns (final_attempt, retries_performed).
    """
    attempt_number = 0
    while True:
        attempt = execute_attempt(
            model_client,
            messages,
            max_output_tokens=max_output_tokens,
            streaming=settings.streaming,
            temperature=settings.temperature,
            top_p=settings.top_p,
            seed=settings.seed,
        )
        if attempt.succeeded or not attempt.is_retryable_failure or attempt_number >= settings.max_retries:
            return attempt, attempt_number
        attempt_number += 1
        sleep_fn(backoff_seconds(attempt_number, rng))


# ---------------------------------------------------------------------------
# Building the final record
# ---------------------------------------------------------------------------


def build_record(
    model_client: ModelClient,
    item: WorkItem,
    *,
    client_request_id: str,
    attempt: AttemptResult,
    retry_count: int,
    settings: BenchmarkSettings,
    region: str,
    pricing_entries: list[PricingEntry],
    as_of: dt.date,
) -> RequestRecord:
    record = RequestRecord(
        benchmark_run_id=settings.run_id,
        prompt_id=item.prompt.prompt_id,
        category=item.prompt.category,
        difficulty=item.prompt.difficulty,
        model=model_client.config.logical_name,
        deployment_name=model_client.config.deployment_name,
        provider=model_client.config.provider,
        region=region,
        repeat=item.repeat,
        streaming=settings.streaming,
        started_at_utc=attempt.started_at_utc,
        completed_at_utc=attempt.completed_at_utc,
        request_id=attempt.request_id,
        client_request_id=client_request_id,
        http_status=attempt.http_status,
        retry_count=retry_count,
        input_tokens=attempt.usage.input_tokens,
        cached_input_tokens=attempt.usage.cached_input_tokens,
        output_tokens=attempt.usage.output_tokens,
        reasoning_tokens=attempt.usage.reasoning_tokens,
        total_tokens=attempt.usage.total_tokens,
        client_latency_ms=attempt.client_latency_ms,
        time_to_first_token_ms=attempt.time_to_first_token_ms,
        generation_time_ms=attempt.generation_time_ms,
        output_tokens_per_second=attempt.output_tokens_per_second,
        finish_reason=attempt.finish_reason,
        response_sha256=hash_text(attempt.content),
        response_text=attempt.content,
        error_type=attempt.error_type,
        error_message=attempt.error_message,
    )
    if attempt.succeeded:
        try:
            pricing_entry = select_pricing_entry(
                pricing_entries,
                provider=model_client.config.provider,
                pricing_key=model_client.config.pricing_key,
                deployment_type=model_client.config.deployment_type,
                region=region,
                as_of=as_of,
            )
            cost = estimate_cost(attempt.usage, pricing_entry)
            record.estimated_input_cost = cost.input_cost
            record.estimated_output_cost = cost.output_cost
            record.estimated_total_cost = cost.total_cost
        except ConfigurationError:
            # No pricing entry — leave cost fields None rather than
            # fail the whole run over a missing price row.
            pass
    return redact_record(record, keep_response_text=settings.store_response_text)


def process_work_item(
    model_client: ModelClient,
    item: WorkItem,
    *,
    settings: BenchmarkSettings,
    region: str,
    pricing_entries: list[PricingEntry],
    as_of: dt.date,
    rng: random.Random,
    sleep_fn: Callable[[float], None],
) -> RequestRecord:
    client_request_id = str(uuid.uuid4())
    max_output_tokens = item.prompt.max_output_tokens
    if settings.max_output_tokens_cap is not None:
        max_output_tokens = min(max_output_tokens, settings.max_output_tokens_cap)
    messages = build_messages(system_instruction=DEFAULT_SYSTEM_INSTRUCTION, user_prompt=item.prompt.prompt)
    attempt, retry_count = execute_with_retries(
        model_client, messages, max_output_tokens=max_output_tokens, settings=settings, rng=rng, sleep_fn=sleep_fn
    )
    return build_record(
        model_client,
        item,
        client_request_id=client_request_id,
        attempt=attempt,
        retry_count=retry_count,
        settings=settings,
        region=region,
        pricing_entries=pricing_entries,
        as_of=as_of,
    )


# ---------------------------------------------------------------------------
# JSONL output + resume support
# ---------------------------------------------------------------------------


class JsonlWriter:
    """Append-only JSONL writer, flushed after every line so an
    interrupted run never loses a fully-written record.
    """

    def __init__(self, path: Path, *, resume: bool) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        mode = "a" if resume and path.exists() else "w"
        self._handle = path.open(mode, encoding="utf-8")

    def write(self, record: RequestRecord) -> None:
        self._handle.write(record.to_json_line() + "\n")
        self._handle.flush()

    def close(self) -> None:
        self._handle.close()

    def __enter__(self) -> "JsonlWriter":
        return self

    def __exit__(self, *_exc) -> None:
        self.close()


def load_records(path: Path, *, run_id: Optional[str] = None) -> list[RequestRecord]:
    """Reads output/requests.jsonl back into RequestRecord objects.
    Filters to `run_id` when given — the file is append-only across
    runs, so a later aggregation pass should usually scope to just the
    run it's summarizing.
    """
    if not path.exists():
        return []
    records = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            data = json.loads(line)
            if run_id is not None and data.get("benchmark_run_id") != run_id:
                continue
            records.append(RequestRecord(**data))
    return records


def load_completed_keys(path: Path, *, run_id: Optional[str] = None) -> set[tuple[str, str, int]]:
    """The (model, prompt_id, repeat) keys already present in
    output/requests.jsonl — used both for resume (skip these) and for
    duplicate detection (spec 2.13).
    """
    return {(record.model, record.prompt_id, record.repeat) for record in load_records(path, run_id=run_id)}


def filter_for_resume(items: list[WorkItem], completed_keys: set[tuple[str, str, int]]) -> list[WorkItem]:
    return [item for item in items if item.key not in completed_keys]


# ---------------------------------------------------------------------------
# Execution
# ---------------------------------------------------------------------------


def execute_items(
    model_clients: dict[str, ModelClient],
    items: list[WorkItem],
    *,
    settings: BenchmarkSettings,
    region: str,
    pricing_entries: list[PricingEntry],
    as_of: dt.date,
    writer: JsonlWriter,
    on_record: Optional[Callable[[RequestRecord], None]] = None,
    sleep_fn: Callable[[float], None] = time.sleep,
) -> list[RequestRecord]:
    """Runs every work item and writes each resulting record as it
    completes. Sequential (`settings.concurrency <= 1`, the default) is
    the latency-measurement mode: one request at a time, with a cooldown
    between them. Concurrency > 1 is a separate throughput-test mode —
    cooldown is skipped (a bounded-concurrency load test isn't trying to
    space requests out), and jitter/backoff reproducibility from
    `settings.seed` is best-effort only, since multiple threads share
    one RNG.
    """
    rng = random.Random(settings.seed)
    records: list[RequestRecord] = []

    if settings.concurrency <= 1:
        for index, item in enumerate(items):
            record = process_work_item(
                model_clients[item.model_logical_name],
                item,
                settings=settings,
                region=region,
                pricing_entries=pricing_entries,
                as_of=as_of,
                rng=rng,
                sleep_fn=sleep_fn,
            )
            records.append(record)
            writer.write(record)
            if on_record:
                on_record(record)
            if index < len(items) - 1:
                sleep_fn(cooldown_seconds(settings, rng))
        return records

    with ThreadPoolExecutor(max_workers=settings.concurrency) as executor:
        futures = {
            executor.submit(
                process_work_item,
                model_clients[item.model_logical_name],
                item,
                settings=settings,
                region=region,
                pricing_entries=pricing_entries,
                as_of=as_of,
                rng=rng,
                sleep_fn=sleep_fn,
            ): item
            for item in items
        }
        for future in as_completed(futures):
            record = future.result()
            records.append(record)
            writer.write(record)
            if on_record:
                on_record(record)
    return records


def run(
    model_clients: dict[str, ModelClient],
    model_configs: list[ModelConfig],
    prompts: list[PromptRecord],
    settings: BenchmarkSettings,
    *,
    region: str,
    pricing_entries: list[PricingEntry],
    output_path: Path,
    resume: bool = False,
    on_record: Optional[Callable[[RequestRecord], None]] = None,
) -> list[RequestRecord]:
    """Top-level orchestration: warm-up, build+filter+order work items,
    optionally drop already-completed ones on resume, execute, write.
    Returns only the records produced by *this* invocation — call
    `load_records(output_path, run_id=settings.run_id)` afterward for
    the full set (including anything skipped via resume).
    """
    filtered_models = filter_models(model_configs, settings)
    filtered_prompts = filter_prompts(prompts, settings)
    items = build_work_items(filtered_models, filtered_prompts, settings)

    if resume:
        completed = load_completed_keys(output_path, run_id=settings.run_id)
        items = filter_for_resume(items, completed)

    run_warm_up(model_clients, settings)

    as_of = dt.datetime.now(dt.timezone.utc).date()
    with JsonlWriter(output_path, resume=resume) as writer:
        return execute_items(
            model_clients,
            items,
            settings=settings,
            region=region,
            pricing_entries=pricing_entries,
            as_of=as_of,
            writer=writer,
            on_record=on_record,
        )
