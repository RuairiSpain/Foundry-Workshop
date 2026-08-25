"""Cost calculation and cached-token pricing (spec 2.13)."""

from __future__ import annotations

import datetime as dt

import pytest

from src.models import ConfigurationError, UsageInfo
from src.pricing import estimate_cost, select_pricing_entry


def test_estimate_cost_uncached(sample_pricing_entries):
    pricing_entry = sample_pricing_entries[0]  # deepseek: input 0.14, cached 0.07, output 0.28 per million
    usage = UsageInfo(input_tokens=1_000_000, output_tokens=1_000_000, cached_input_tokens=0)

    cost = estimate_cost(usage, pricing_entry)

    assert cost.input_cost == pytest.approx(0.14)
    assert cost.output_cost == pytest.approx(0.28)
    assert cost.total_cost == pytest.approx(0.42)


def test_estimate_cost_with_cached_tokens_uses_the_cheaper_rate(sample_pricing_entries):
    pricing_entry = sample_pricing_entries[0]
    usage = UsageInfo(input_tokens=1_000_000, cached_input_tokens=1_000_000, output_tokens=0)

    cost = estimate_cost(usage, pricing_entry)

    # All 1M input tokens were cached: billed at cached rate, not full input rate.
    assert cost.input_cost == pytest.approx(0.07)


def test_estimate_cost_mixed_cached_and_uncached(sample_pricing_entries):
    pricing_entry = sample_pricing_entries[0]
    usage = UsageInfo(input_tokens=1_000_000, cached_input_tokens=400_000, output_tokens=0)

    cost = estimate_cost(usage, pricing_entry)

    expected = (600_000 / 1_000_000) * 0.14 + (400_000 / 1_000_000) * 0.07
    assert cost.input_cost == pytest.approx(expected)


def test_estimate_cost_clamps_cached_tokens_to_input_tokens(sample_pricing_entries):
    """A provider reporting cached_input_tokens > input_tokens (a data
    quality issue, not something the cost calculator should crash on)
    doesn't produce a negative uncached-token count.
    """
    pricing_entry = sample_pricing_entries[0]
    usage = UsageInfo(input_tokens=100, cached_input_tokens=500, output_tokens=0)

    cost = estimate_cost(usage, pricing_entry)

    assert cost.input_cost == pytest.approx(100 / 1_000_000 * 0.07)


def test_estimate_cost_missing_usage_treated_as_zero(sample_pricing_entries):
    pricing_entry = sample_pricing_entries[0]
    usage = UsageInfo()  # every field None

    cost = estimate_cost(usage, pricing_entry)

    assert cost.total_cost == 0.0


def test_estimate_cost_rounds_to_six_decimal_places(sample_pricing_entries):
    pricing_entry = sample_pricing_entries[0]
    usage = UsageInfo(input_tokens=1, output_tokens=1)

    cost = estimate_cost(usage, pricing_entry)

    assert cost.total_cost == round(cost.total_cost, 6)


# --- pricing selection --------------------------------------------------------


def test_select_pricing_entry_matches_provider_model_deployment_type_region(sample_pricing_entries):
    entry = select_pricing_entry(
        sample_pricing_entries,
        provider="deepseek",
        pricing_key="deepseek-v4-flash",
        deployment_type="serverless",
        region="eastus",
        as_of=dt.date(2026, 6, 1),
    )
    assert entry.provider == "deepseek"


def test_select_pricing_entry_raises_when_nothing_matches(sample_pricing_entries):
    with pytest.raises(ConfigurationError, match="No pricing entry found"):
        select_pricing_entry(
            sample_pricing_entries,
            provider="deepseek",
            pricing_key="does-not-exist",
            deployment_type="serverless",
            region="eastus",
            as_of=dt.date(2026, 6, 1),
        )


def test_select_pricing_entry_picks_latest_effective_date_not_later_than_as_of():
    from src.models import PricingEntry

    entries = [
        PricingEntry(
            provider="deepseek",
            model="m",
            deployment_type="serverless",
            region="any",
            input_price_per_million=1.0,
            cached_input_price_per_million=0.5,
            output_price_per_million=2.0,
            currency="USD",
            effective_date=dt.date(2026, 1, 1),
            source="manual-verified",
        ),
        PricingEntry(
            provider="deepseek",
            model="m",
            deployment_type="serverless",
            region="any",
            input_price_per_million=0.5,  # a later, cheaper price
            cached_input_price_per_million=0.25,
            output_price_per_million=1.0,
            currency="USD",
            effective_date=dt.date(2026, 6, 1),
            source="manual-verified",
        ),
    ]

    # As of a date before the price drop: the older, higher price applies.
    entry = select_pricing_entry(entries, provider="deepseek", pricing_key="m", deployment_type="serverless", region="any", as_of=dt.date(2026, 3, 1))
    assert entry.input_price_per_million == 1.0

    # As of a date after the price drop: the newer, cheaper price applies.
    entry = select_pricing_entry(entries, provider="deepseek", pricing_key="m", deployment_type="serverless", region="any", as_of=dt.date(2026, 12, 1))
    assert entry.input_price_per_million == 0.5


def test_select_pricing_entry_region_specific_outranks_any_on_same_date():
    from src.models import PricingEntry

    entries = [
        PricingEntry(
            provider="deepseek",
            model="m",
            deployment_type="serverless",
            region="any",
            input_price_per_million=1.0,
            cached_input_price_per_million=0.5,
            output_price_per_million=2.0,
            currency="USD",
            effective_date=dt.date(2026, 1, 1),
            source="manual-verified",
        ),
        PricingEntry(
            provider="deepseek",
            model="m",
            deployment_type="serverless",
            region="eastus",
            input_price_per_million=1.5,
            cached_input_price_per_million=0.75,
            output_price_per_million=3.0,
            currency="USD",
            effective_date=dt.date(2026, 1, 1),
            source="manual-verified",
        ),
    ]

    entry = select_pricing_entry(entries, provider="deepseek", pricing_key="m", deployment_type="serverless", region="eastus", as_of=dt.date(2026, 6, 1))
    assert entry.region == "eastus"
