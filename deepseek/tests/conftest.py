"""Shared fixtures. All Azure/OpenAI SDK objects here are lightweight
fakes with just the attributes `inference_client.py` reads — no real
SDK classes are imported by these fixtures, so unit tests never touch
the network.
"""

from __future__ import annotations

import datetime as dt

import pytest

from src.client_factory import ModelClient
from src.models import BenchmarkSettings, ModelConfig, PricingEntry, PromptRecord


@pytest.fixture
def deepseek_config() -> ModelConfig:
    return ModelConfig(
        logical_name="deepseek-v4-flash",
        deployment_name="deepseek-v4-flash-3107",
        provider="deepseek",
        pricing_key="deepseek-v4-flash",
        deployment_type="serverless",
    )


@pytest.fixture
def azure_openai_config() -> ModelConfig:
    return ModelConfig(
        logical_name="gpt-5-sol",
        deployment_name="gpt-5-sol",
        provider="azure-openai",
        pricing_key="gpt-5",
        deployment_type="standard",
    )


@pytest.fixture
def sample_prompt() -> PromptRecord:
    return PromptRecord(
        prompt_id="TEST-001",
        category="classification",
        difficulty="simple",
        max_output_tokens=60,
        prompt="Classify this.",
    )


@pytest.fixture
def sample_pricing_entries() -> list[PricingEntry]:
    return [
        PricingEntry(
            provider="deepseek",
            model="deepseek-v4-flash",
            deployment_type="serverless",
            region="any",
            input_price_per_million=0.14,
            cached_input_price_per_million=0.07,
            output_price_per_million=0.28,
            currency="USD",
            effective_date=dt.date(2026, 1, 1),
            source="manual-placeholder",
        ),
        PricingEntry(
            provider="azure-openai",
            model="gpt-5",
            deployment_type="standard",
            region="any",
            input_price_per_million=1.75,
            cached_input_price_per_million=0.44,
            output_price_per_million=7.00,
            currency="USD",
            effective_date=dt.date(2026, 1, 1),
            source="manual-placeholder",
        ),
    ]


@pytest.fixture
def default_settings() -> BenchmarkSettings:
    return BenchmarkSettings(
        run_id="test-run-0001",
        warm_up_count=0,
        repeats=1,
        concurrency=1,
        streaming=False,
        cooldown_ms_min=0,
        cooldown_ms_max=1,
        max_retries=2,
        seed=42,
    )


def make_model_client(config: ModelConfig, backend: str, fake_sdk_client) -> ModelClient:
    return ModelClient(config=config, backend=backend, client=fake_sdk_client)
