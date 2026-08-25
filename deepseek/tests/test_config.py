"""Configuration validation: config/models.yaml, config/pricing.yaml,
data/prompts.jsonl, and environment settings (spec 2.13).
"""

from __future__ import annotations

import textwrap

import pytest

from src.client_factory import EnvironmentSettings, load_model_configs
from src.cli import load_prompts
from src.models import ConfigurationError
from src.pricing import load_pricing_table


def _write(path, content: str):
    path.write_text(textwrap.dedent(content), encoding="utf-8")
    return path


# --- models.yaml -----------------------------------------------------------


def test_load_model_configs_happy_path(tmp_path):
    path = _write(
        tmp_path / "models.yaml",
        """
        models:
          - logical_name: a
            deployment_name: dep-a
            provider: deepseek
            pricing_key: a
          - logical_name: b
            deployment_name: dep-b
            provider: azure-openai
            pricing_key: b
            enabled: false
        """,
    )
    configs = load_model_configs(path)
    assert [c.logical_name for c in configs] == ["a", "b"]
    assert configs[1].enabled is False


def test_load_model_configs_missing_file(tmp_path):
    with pytest.raises(ConfigurationError, match="not found"):
        load_model_configs(tmp_path / "does-not-exist.yaml")


def test_load_model_configs_rejects_duplicate_logical_name(tmp_path):
    path = _write(
        tmp_path / "models.yaml",
        """
        models:
          - logical_name: a
            deployment_name: dep-a
            provider: deepseek
            pricing_key: a
          - logical_name: a
            deployment_name: dep-b
            provider: deepseek
            pricing_key: a
        """,
    )
    with pytest.raises(ConfigurationError, match="Duplicate logical_name"):
        load_model_configs(path)


def test_load_model_configs_rejects_duplicate_deployment_name(tmp_path):
    path = _write(
        tmp_path / "models.yaml",
        """
        models:
          - logical_name: a
            deployment_name: dep-shared
            provider: deepseek
            pricing_key: a
          - logical_name: b
            deployment_name: dep-shared
            provider: deepseek
            pricing_key: a
        """,
    )
    with pytest.raises(ConfigurationError, match="Duplicate deployment_name"):
        load_model_configs(path)


def test_load_model_configs_rejects_unknown_provider(tmp_path):
    path = _write(
        tmp_path / "models.yaml",
        """
        models:
          - logical_name: a
            deployment_name: dep-a
            provider: not-a-real-provider
            pricing_key: a
        """,
    )
    with pytest.raises(ConfigurationError, match="unknown provider"):
        load_model_configs(path)


def test_load_model_configs_rejects_all_disabled(tmp_path):
    path = _write(
        tmp_path / "models.yaml",
        """
        models:
          - logical_name: a
            deployment_name: dep-a
            provider: deepseek
            pricing_key: a
            enabled: false
        """,
    )
    with pytest.raises(ConfigurationError, match="enabled: false"):
        load_model_configs(path)


def test_load_model_configs_rejects_missing_required_field(tmp_path):
    path = _write(
        tmp_path / "models.yaml",
        """
        models:
          - logical_name: a
            provider: deepseek
            pricing_key: a
        """,
    )
    with pytest.raises(ConfigurationError, match="missing required field"):
        load_model_configs(path)


# --- pricing.yaml ------------------------------------------------------------


def test_load_pricing_table_happy_path(tmp_path):
    path = _write(
        tmp_path / "pricing.yaml",
        """
        pricing_version: "v1"
        entries:
          - provider: deepseek
            model: m
            deployment_type: serverless
            region: any
            input_price_per_million: 1.0
            cached_input_price_per_million: 0.5
            output_price_per_million: 2.0
            currency: USD
            effective_date: "2026-01-01"
            source: manual-verified
        """,
    )
    version, entries = load_pricing_table(path)
    assert version == "v1"
    assert len(entries) == 1


def test_load_pricing_table_rejects_missing_version(tmp_path):
    path = _write(tmp_path / "pricing.yaml", "entries: []")
    with pytest.raises(ConfigurationError, match="pricing_version"):
        load_pricing_table(path)


def test_load_pricing_table_rejects_empty_entries(tmp_path):
    path = _write(tmp_path / "pricing.yaml", 'pricing_version: "v1"\nentries: []')
    with pytest.raises(ConfigurationError, match="no pricing entries"):
        load_pricing_table(path)


# --- prompts.jsonl -----------------------------------------------------------


def test_load_prompts_happy_path(tmp_path):
    path = tmp_path / "prompts.jsonl"
    path.write_text(
        '{"prompt_id":"P1","category":"c","difficulty":"simple","max_output_tokens":10,"prompt":"hi"}\n'
        '{"prompt_id":"P2","category":"c","difficulty":"simple","max_output_tokens":10,"prompt":"there"}\n',
        encoding="utf-8",
    )
    prompts = load_prompts(path)
    assert [p.prompt_id for p in prompts] == ["P1", "P2"]


def test_load_prompts_missing_file(tmp_path):
    with pytest.raises(ConfigurationError, match="not found"):
        load_prompts(tmp_path / "missing.jsonl")


def test_load_prompts_rejects_invalid_json(tmp_path):
    path = tmp_path / "prompts.jsonl"
    path.write_text("{not valid json\n", encoding="utf-8")
    with pytest.raises(ConfigurationError, match="not valid JSON"):
        load_prompts(path)


def test_load_prompts_rejects_duplicate_prompt_id(tmp_path):
    path = tmp_path / "prompts.jsonl"
    path.write_text(
        '{"prompt_id":"P1","category":"c","difficulty":"simple","max_output_tokens":10,"prompt":"hi"}\n'
        '{"prompt_id":"P1","category":"c","difficulty":"simple","max_output_tokens":10,"prompt":"again"}\n',
        encoding="utf-8",
    )
    with pytest.raises(ConfigurationError, match="duplicate prompt_id"):
        load_prompts(path)


def test_load_prompts_rejects_zero_max_output_tokens(tmp_path):
    path = tmp_path / "prompts.jsonl"
    path.write_text('{"prompt_id":"P1","category":"c","difficulty":"simple","max_output_tokens":0,"prompt":"hi"}\n', encoding="utf-8")
    with pytest.raises(ConfigurationError, match="invalid max_output_tokens"):
        load_prompts(path)


def test_load_prompts_ignores_blank_lines(tmp_path):
    path = tmp_path / "prompts.jsonl"
    path.write_text(
        '{"prompt_id":"P1","category":"c","difficulty":"simple","max_output_tokens":10,"prompt":"hi"}\n\n   \n',
        encoding="utf-8",
    )
    prompts = load_prompts(path)
    assert len(prompts) == 1


def test_load_prompts_rejects_empty_file(tmp_path):
    path = tmp_path / "prompts.jsonl"
    path.write_text("", encoding="utf-8")
    with pytest.raises(ConfigurationError, match="no prompts"):
        load_prompts(path)


# --- environment settings -----------------------------------------------------


def test_environment_settings_requires_foundry_endpoint():
    with pytest.raises(ConfigurationError, match="AZURE_FOUNDRY_ENDPOINT"):
        EnvironmentSettings.from_env({})


def test_environment_settings_defaults():
    settings = EnvironmentSettings.from_env({"AZURE_FOUNDRY_ENDPOINT": "https://example.services.ai.azure.com/"})
    assert settings.foundry_endpoint == "https://example.services.ai.azure.com"
    assert settings.use_api_key_fallback is False
    assert settings.benchmark_run_id  # a default timestamp was generated


def test_environment_settings_require_azure_monitor_config_lists_missing():
    settings = EnvironmentSettings.from_env({"AZURE_FOUNDRY_ENDPOINT": "https://x"})
    with pytest.raises(ConfigurationError, match="AZURE_SUBSCRIPTION_ID"):
        settings.require_azure_monitor_config()


def test_environment_settings_require_azure_monitor_config_passes_when_set():
    settings = EnvironmentSettings.from_env(
        {
            "AZURE_FOUNDRY_ENDPOINT": "https://x",
            "AZURE_SUBSCRIPTION_ID": "sub",
            "AZURE_RESOURCE_GROUP": "rg",
            "AZURE_FOUNDRY_RESOURCE_NAME": "res",
        }
    )
    settings.require_azure_monitor_config()  # does not raise
