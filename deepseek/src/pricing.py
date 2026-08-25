"""Cost estimation from the versioned config/pricing.yaml table.

Per spec 2.12: use SDK token counts + this config file for immediate
estimated costs. Azure Cost Management is the later, authoritative
billing-reconciliation source — Microsoft documents an approximate
five-hour delay before model consumption appears there, so the
benchmark never waits on it.
"""

from __future__ import annotations

import dataclasses
import datetime as dt
from pathlib import Path
from typing import Optional

import yaml

from .models import ConfigurationError, PricingEntry, UsageInfo


@dataclasses.dataclass
class CostEstimate:
    input_cost: float
    output_cost: float
    total_cost: float
    pricing_entry: PricingEntry


def load_pricing_table(path: Path) -> tuple[str, list[PricingEntry]]:
    """Loads config/pricing.yaml. Returns (pricing_version, entries)."""
    if not path.exists():
        raise ConfigurationError(f"Pricing file not found: {path}")
    with path.open("r", encoding="utf-8") as handle:
        raw = yaml.safe_load(handle) or {}
    version = raw.get("pricing_version")
    if not version:
        raise ConfigurationError(f"{path} is missing top-level 'pricing_version'.")
    raw_entries = raw.get("entries") or []
    if not raw_entries:
        raise ConfigurationError(f"{path} has no pricing entries under 'entries'.")
    entries = [PricingEntry.from_dict(entry) for entry in raw_entries]
    return version, entries


def select_pricing_entry(
    entries: list[PricingEntry],
    *,
    provider: str,
    pricing_key: str,
    deployment_type: str,
    region: str,
    as_of: dt.date,
) -> PricingEntry:
    """Selects the entry with the latest effective_date <= `as_of`
    matching provider, pricing_key, and deployment_type. `region`
    matches an entry whose region equals `region` or is "any".

    Raises ConfigurationError if no matching entry exists — a silent
    fallback to a wrong price is worse than a loud, fixable error.
    """
    candidates = [
        entry
        for entry in entries
        if entry.provider == provider
        and entry.model == pricing_key
        and entry.deployment_type == deployment_type
        and entry.region in (region, "any")
        and entry.effective_date <= as_of
    ]
    if not candidates:
        raise ConfigurationError(
            f"No pricing entry found for provider={provider!r} model={pricing_key!r} "
            f"deployment_type={deployment_type!r} region={region!r} as_of={as_of.isoformat()}. "
            f"Check config/pricing.yaml."
        )
    # Latest effective_date wins; region-specific entries outrank "any" on a tie.
    candidates.sort(key=lambda entry: (entry.effective_date, entry.region != "any"))
    return candidates[-1]


def estimate_cost(usage: UsageInfo, pricing_entry: PricingEntry) -> CostEstimate:
    """Computes cost from token usage and a pricing entry.

    Cached input tokens are billed at `cached_input_price_per_million`
    instead of the full input price; uncached input tokens make up the
    rest of `input_tokens`. Missing token counts are treated as 0 for
    the cost calculation (the RequestRecord still records them as
    None, so "no cost because no usage" and "zero-cost usage" stay
    distinguishable at the record level).
    """
    input_tokens = usage.input_tokens or 0
    cached_tokens = min(usage.cached_input_tokens or 0, input_tokens)
    uncached_tokens = input_tokens - cached_tokens
    output_tokens = usage.output_tokens or 0

    input_cost = (
        uncached_tokens / 1_000_000 * pricing_entry.input_price_per_million
        + cached_tokens / 1_000_000 * pricing_entry.cached_input_price_per_million
    )
    output_cost = output_tokens / 1_000_000 * pricing_entry.output_price_per_million
    return CostEstimate(
        input_cost=round(input_cost, 6),
        output_cost=round(output_cost, 6),
        total_cost=round(input_cost + output_cost, 6),
        pricing_entry=pricing_entry,
    )
