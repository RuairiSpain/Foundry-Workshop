"""Typed data structures shared across the benchmark: configuration,
per-request records, and aggregation output rows.

Kept dependency-free (stdlib `dataclasses` only) so every other module
can import from here without pulling in a validation framework.
"""

from __future__ import annotations

import dataclasses
import datetime as dt
import hashlib
import json
from typing import Any, Optional


class ConfigurationError(Exception):
    """Raised for a malformed or incomplete configuration file.

    Distinct from `DeploymentResolutionError` — this is a problem with
    the YAML/JSONL itself (missing field, bad type, duplicate ID),
    caught before any network call is made.
    """


class DeploymentResolutionError(Exception):
    """Raised when a configured deployment can't be resolved against the
    real Foundry project — e.g. the first request against it 404s.

    Carries the deployment name and provider so the CLI can print a
    clear, actionable error instead of a raw SDK traceback.
    """

    def __init__(self, logical_name: str, deployment_name: str, provider: str, detail: str) -> None:
        self.logical_name = logical_name
        self.deployment_name = deployment_name
        self.provider = provider
        self.detail = detail
        super().__init__(
            f"Could not resolve deployment '{deployment_name}' (logical name '{logical_name}', "
            f"provider '{provider}'): {detail}. Confirm this deployment exists in your Foundry "
            f"project and that config/models.yaml has the exact deployment name, not the catalog "
            f"model ID."
        )


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------


@dataclasses.dataclass(frozen=True)
class ModelConfig:
    """One entry from config/models.yaml.

    The `supports_*` flags default to True (the recommended baseline
    parameters from spec 2.5 apply). Some deployments — reasoning
    models in particular — reject a fixed temperature, top_p, or seed
    with a 400 error. Per spec 2.5 ("record unsupported parameters
    rather than silently changing them"), the client does not catch
    that error and quietly retry without the parameter: instead, the
    first run against a new deployment is expected to surface the
    rejection as a normal failed RequestRecord
    (error_type="unsupported_parameter"), and the operator then flips
    the matching `supports_*` flag to false here — an explicit,
    recorded configuration decision for every subsequent run, not a
    runtime guess.
    """

    logical_name: str
    deployment_name: str
    provider: str  # "azure-openai" | "deepseek" | (future providers)
    pricing_key: str
    deployment_type: str = "standard"
    enabled: bool = True
    supports_temperature: bool = True
    supports_top_p: bool = True
    supports_seed: bool = True

    @staticmethod
    def from_dict(data: dict) -> "ModelConfig":
        required = ["logical_name", "deployment_name", "provider", "pricing_key"]
        missing = [field for field in required if not data.get(field)]
        if missing:
            raise ConfigurationError(f"models.yaml entry is missing required field(s): {missing} (entry: {data!r})")
        if data["provider"] not in ("azure-openai", "deepseek"):
            raise ConfigurationError(
                f"models.yaml entry '{data['logical_name']}' has unknown provider "
                f"'{data['provider']}' — expected 'azure-openai' or 'deepseek'."
            )
        return ModelConfig(
            logical_name=data["logical_name"],
            deployment_name=data["deployment_name"],
            provider=data["provider"],
            pricing_key=data["pricing_key"],
            deployment_type=data.get("deployment_type", "standard"),
            enabled=bool(data.get("enabled", True)),
            supports_temperature=bool(data.get("supports_temperature", True)),
            supports_top_p=bool(data.get("supports_top_p", True)),
            supports_seed=bool(data.get("supports_seed", True)),
        )


@dataclasses.dataclass(frozen=True)
class PricingEntry:
    """One entry from config/pricing.yaml."""

    provider: str
    model: str
    deployment_type: str
    region: str
    input_price_per_million: float
    cached_input_price_per_million: float
    output_price_per_million: float
    currency: str
    effective_date: dt.date
    source: str

    @staticmethod
    def from_dict(data: dict) -> "PricingEntry":
        required = [
            "provider",
            "model",
            "deployment_type",
            "region",
            "input_price_per_million",
            "cached_input_price_per_million",
            "output_price_per_million",
            "currency",
            "effective_date",
            "source",
        ]
        missing = [field for field in required if data.get(field) is None]
        if missing:
            raise ConfigurationError(f"pricing.yaml entry is missing required field(s): {missing} (entry: {data!r})")
        return PricingEntry(
            provider=data["provider"],
            model=data["model"],
            deployment_type=data["deployment_type"],
            region=data["region"],
            input_price_per_million=float(data["input_price_per_million"]),
            cached_input_price_per_million=float(data["cached_input_price_per_million"]),
            output_price_per_million=float(data["output_price_per_million"]),
            currency=data["currency"],
            effective_date=_parse_date(data["effective_date"]),
            source=data["source"],
        )


def _parse_date(value: Any) -> dt.date:
    if isinstance(value, dt.date):
        return value
    return dt.date.fromisoformat(str(value))


@dataclasses.dataclass(frozen=True)
class PromptRecord:
    """One line from data/prompts.jsonl."""

    prompt_id: str
    category: str
    difficulty: str
    max_output_tokens: int
    prompt: str

    @staticmethod
    def from_dict(data: dict) -> "PromptRecord":
        required = ["prompt_id", "category", "difficulty", "max_output_tokens", "prompt"]
        missing = [field for field in required if data.get(field) is None]
        if missing:
            raise ConfigurationError(f"prompts.jsonl line is missing required field(s): {missing} (entry: {data!r})")
        if not isinstance(data["max_output_tokens"], int) or data["max_output_tokens"] <= 0:
            raise ConfigurationError(
                f"prompts.jsonl entry '{data['prompt_id']}' has an invalid max_output_tokens: "
                f"{data['max_output_tokens']!r} (must be a positive integer)"
            )
        return PromptRecord(
            prompt_id=data["prompt_id"],
            category=data["category"],
            difficulty=data["difficulty"],
            max_output_tokens=data["max_output_tokens"],
            prompt=data["prompt"],
        )


@dataclasses.dataclass(frozen=True)
class BenchmarkSettings:
    """Execution parameters for one benchmark run (spec 2.5 / 2.6)."""

    run_id: str
    warm_up_count: int = 3
    repeats: int = 5
    concurrency: int = 1
    streaming: bool = True
    temperature: float = 0.0
    top_p: float = 1.0
    max_output_tokens_cap: Optional[int] = 500
    seed: Optional[int] = 42
    cooldown_ms_min: int = 500
    cooldown_ms_max: int = 1000
    max_retries: int = 3
    randomize_model_order: bool = True
    randomize_prompt_order: bool = True
    store_response_text: bool = True
    dry_run: bool = False
    category_filter: Optional[str] = None
    model_filter: Optional[str] = None
    difficulty_filter: Optional[str] = None


# ---------------------------------------------------------------------------
# Usage normalization
# ---------------------------------------------------------------------------


@dataclasses.dataclass
class UsageInfo:
    """Token usage normalized across providers.

    Fields the provider didn't return stay `None` rather than being
    coerced to 0 — "the service didn't tell us" and "the service told
    us zero" are different facts (spec 2.13: "missing usage fields").
    """

    input_tokens: Optional[int] = None
    cached_input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    reasoning_tokens: Optional[int] = None
    total_tokens: Optional[int] = None

    def __post_init__(self) -> None:
        if self.total_tokens is None and self.input_tokens is not None and self.output_tokens is not None:
            self.total_tokens = self.input_tokens + self.output_tokens


# ---------------------------------------------------------------------------
# Per-request record (spec 2.7)
# ---------------------------------------------------------------------------


@dataclasses.dataclass
class RequestRecord:
    benchmark_run_id: str
    prompt_id: str
    category: str
    difficulty: str
    model: str
    deployment_name: str
    provider: str
    region: str
    repeat: int
    streaming: bool
    started_at_utc: str
    completed_at_utc: str
    request_id: Optional[str] = None
    client_request_id: str = ""
    http_status: Optional[int] = None
    retry_count: int = 0
    input_tokens: Optional[int] = None
    cached_input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    reasoning_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    client_latency_ms: Optional[float] = None
    time_to_first_token_ms: Optional[float] = None
    generation_time_ms: Optional[float] = None
    output_tokens_per_second: Optional[float] = None
    finish_reason: Optional[str] = None
    estimated_input_cost: Optional[float] = None
    estimated_output_cost: Optional[float] = None
    estimated_total_cost: Optional[float] = None
    response_sha256: Optional[str] = None
    response_text: Optional[str] = None
    error_type: Optional[str] = None
    error_message: Optional[str] = None

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)

    def to_json_line(self) -> str:
        return json.dumps(self.to_dict(), default=str, sort_keys=False)

    @property
    def succeeded(self) -> bool:
        return self.error_type is None and self.http_status is not None and 200 <= self.http_status < 300

    @property
    def throttled(self) -> bool:
        return self.http_status == 429


def hash_text(text: Optional[str]) -> Optional[str]:
    """SHA-256 hex digest of `text`, or None if `text` is None."""
    if text is None:
        return None
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def redact_record(record: RequestRecord, *, keep_response_text: bool) -> RequestRecord:
    """Returns a copy of `record` with `response_text` cleared when
    `keep_response_text` is False. `response_sha256` is always kept —
    it lets a reviewer confirm two runs produced identical output
    without storing the content itself.
    """
    if keep_response_text:
        return record
    return dataclasses.replace(record, response_text=None)


# ---------------------------------------------------------------------------
# Aggregation output (spec 2.11 / section 4)
# ---------------------------------------------------------------------------


@dataclasses.dataclass
class ModelSummaryRow:
    model: str
    category: str
    requests_attempted: int
    requests_succeeded: int
    requests_failed: int
    throttled_requests: int
    retry_rate: float
    input_tokens: int
    output_tokens: int
    total_tokens: int
    mean_latency_ms: Optional[float]
    median_latency_ms: Optional[float]
    p50_latency_ms: Optional[float]
    p90_latency_ms: Optional[float]
    p95_latency_ms: Optional[float]
    p99_latency_ms: Optional[float]
    median_ttft_ms: Optional[float]
    p95_ttft_ms: Optional[float]
    median_output_tokens_per_second: Optional[float]
    estimated_total_cost: float
    estimated_cost_per_request: float
    estimated_cost_per_1000_requests: float

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)


@dataclasses.dataclass
class ReconciliationRow:
    model: str
    deployment_name: str
    metric: str
    sdk_value: Optional[float]
    azure_monitor_value: Optional[float]
    difference: Optional[float]
    difference_pct: Optional[float]
    notes: str = ""

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)
