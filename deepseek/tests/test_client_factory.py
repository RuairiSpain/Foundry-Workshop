"""Client construction dispatch and authentication resolution — SDK
constructors are monkeypatched so these tests never touch the network
or need real credentials.
"""

from __future__ import annotations

import pytest

from src import client_factory as cf
from src.models import ConfigurationError, DeploymentResolutionError


def test_resolve_auth_defaults_to_entra_id(monkeypatch):
    class FakeDefaultAzureCredential:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    monkeypatch.setattr("azure.identity.DefaultAzureCredential", FakeDefaultAzureCredential)
    settings = cf.EnvironmentSettings.from_env({"AZURE_FOUNDRY_ENDPOINT": "https://x"})

    auth = cf.resolve_auth(settings)

    assert auth.mode == "entra_id"
    assert isinstance(auth.token_credential, FakeDefaultAzureCredential)


def test_resolve_auth_uses_api_key_only_when_explicitly_opted_in():
    settings = cf.EnvironmentSettings.from_env(
        {"AZURE_FOUNDRY_ENDPOINT": "https://x", "AZURE_FOUNDRY_USE_API_KEY": "true", "AZURE_FOUNDRY_API_KEY": "secret-key"}
    )
    auth = cf.resolve_auth(settings)
    assert auth.mode == "api_key"
    assert auth.api_key == "secret-key"


def test_resolve_auth_requires_api_key_when_fallback_opted_in_but_key_missing():
    settings = cf.EnvironmentSettings.from_env({"AZURE_FOUNDRY_ENDPOINT": "https://x", "AZURE_FOUNDRY_USE_API_KEY": "true"})
    with pytest.raises(ConfigurationError, match="AZURE_FOUNDRY_API_KEY"):
        cf.resolve_auth(settings)


def test_build_model_client_dispatches_azure_openai(monkeypatch, azure_openai_config):
    calls = {}

    class FakeAzureOpenAI:
        def __init__(self, **kwargs):
            calls.update(kwargs)

    monkeypatch.setattr("openai.AzureOpenAI", FakeAzureOpenAI)
    settings = cf.EnvironmentSettings.from_env({"AZURE_FOUNDRY_ENDPOINT": "https://x", "AZURE_FOUNDRY_USE_API_KEY": "true", "AZURE_FOUNDRY_API_KEY": "k"})
    auth = cf.resolve_auth(settings)

    model_client = cf.build_model_client(azure_openai_config, settings, auth)

    assert model_client.backend == "azure-openai"
    assert isinstance(model_client.client, FakeAzureOpenAI)
    assert calls["api_key"] == "k"


def test_build_model_client_dispatches_deepseek(monkeypatch, deepseek_config):
    calls = {}

    class FakeChatCompletionsClient:
        def __init__(self, **kwargs):
            calls.update(kwargs)

    monkeypatch.setattr("azure.ai.inference.ChatCompletionsClient", FakeChatCompletionsClient)
    settings = cf.EnvironmentSettings.from_env({"AZURE_FOUNDRY_ENDPOINT": "https://x", "AZURE_FOUNDRY_USE_API_KEY": "true", "AZURE_FOUNDRY_API_KEY": "k"})
    auth = cf.resolve_auth(settings)

    model_client = cf.build_model_client(deepseek_config, settings, auth)

    assert model_client.backend == "azure-ai-inference"
    assert isinstance(model_client.client, FakeChatCompletionsClient)


def test_build_model_clients_skips_disabled_entries(monkeypatch, deepseek_config, azure_openai_config):
    import dataclasses

    disabled = dataclasses.replace(azure_openai_config, enabled=False)
    monkeypatch.setattr("azure.ai.inference.ChatCompletionsClient", lambda **kwargs: object())
    monkeypatch.setattr("openai.AzureOpenAI", lambda **kwargs: object())
    settings = cf.EnvironmentSettings.from_env({"AZURE_FOUNDRY_ENDPOINT": "https://x", "AZURE_FOUNDRY_USE_API_KEY": "true", "AZURE_FOUNDRY_API_KEY": "k"})
    auth = cf.resolve_auth(settings)

    clients = cf.build_model_clients([deepseek_config, disabled], settings, auth)

    assert set(clients.keys()) == {deepseek_config.logical_name}


def test_validate_deployment_live_wraps_failure_as_deployment_resolution_error(deepseek_config):
    class FailingSdk:
        def complete(self, **kwargs):
            raise RuntimeError("404 deployment not found")

    from src.client_factory import ModelClient

    model_client = ModelClient(config=deepseek_config, backend="azure-ai-inference", client=FailingSdk())
    with pytest.raises(DeploymentResolutionError, match="deepseek-v4-flash-3107"):
        cf.validate_deployment_live(model_client)


def test_validate_deployment_live_succeeds_silently_when_call_works(deepseek_config):
    class WorkingSdk:
        def complete(self, **kwargs):
            return object()

    from src.client_factory import ModelClient

    model_client = ModelClient(config=deepseek_config, backend="azure-ai-inference", client=WorkingSdk())
    cf.validate_deployment_live(model_client)  # does not raise
