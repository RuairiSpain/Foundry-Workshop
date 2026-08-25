"""Configuration loading, authentication, and per-deployment client
construction.

Verified against the actually-installed SDKs before writing this
module (not from memory or docs):
  - `azure.ai.inference.ChatCompletionsClient.__init__(endpoint, credential, ...)`
    and `.complete(messages=, stream=, model=, temperature=, top_p=,
    max_tokens=, seed=, ...)` — `azure-ai-inference` 1.0.0b9.
  - `openai.AzureOpenAI.__init__(azure_endpoint=, api_version=, api_key=,
    azure_ad_token_provider=, ...)` — `openai` 2.54.0.
  - `azure.identity.DefaultAzureCredential`,
    `azure.identity.get_bearer_token_provider` — `azure-identity` 1.25.3.
"""

from __future__ import annotations

import dataclasses
import os
from pathlib import Path
from typing import Optional, Union

import yaml
from azure.core.credentials import AzureKeyCredential, TokenCredential

from .models import ConfigurationError, DeploymentResolutionError, ModelConfig

# Cognitive Services' own scope. Both azure-ai-inference's Foundry Models
# endpoint and Azure OpenAI's control plane sit under Cognitive Services
# in Entra ID, so the same scope covers both backends.
_COGNITIVE_SERVICES_SCOPE = "https://cognitiveservices.azure.com/.default"


# ---------------------------------------------------------------------------
# Environment configuration
# ---------------------------------------------------------------------------


@dataclasses.dataclass(frozen=True)
class EnvironmentSettings:
    """Required and optional environment variables (spec 2.4)."""

    foundry_endpoint: str
    api_version: str
    subscription_id: Optional[str]
    resource_group: Optional[str]
    foundry_resource_name: Optional[str]
    log_analytics_workspace_id: Optional[str]
    application_insights_connection_string: Optional[str]
    benchmark_run_id: str
    region: str
    api_key: Optional[str]
    use_api_key_fallback: bool

    @staticmethod
    def from_env(env: Optional[dict] = None) -> "EnvironmentSettings":
        env = env if env is not None else os.environ
        endpoint = env.get("AZURE_FOUNDRY_ENDPOINT")
        if not endpoint:
            raise ConfigurationError(
                "AZURE_FOUNDRY_ENDPOINT is not set. It must point at your Foundry project's "
                "inference endpoint, e.g. https://<project>.services.ai.azure.com."
            )
        run_id = env.get("BENCHMARK_RUN_ID") or default_run_id()
        return EnvironmentSettings(
            foundry_endpoint=endpoint.rstrip("/"),
            api_version=env.get("AZURE_FOUNDRY_API_VERSION", "2026-01-01-preview"),
            subscription_id=env.get("AZURE_SUBSCRIPTION_ID"),
            resource_group=env.get("AZURE_RESOURCE_GROUP"),
            foundry_resource_name=env.get("AZURE_FOUNDRY_RESOURCE_NAME"),
            log_analytics_workspace_id=env.get("AZURE_LOG_ANALYTICS_WORKSPACE_ID"),
            application_insights_connection_string=env.get("APPLICATIONINSIGHTS_CONNECTION_STRING"),
            benchmark_run_id=run_id,
            region=env.get("AZURE_FOUNDRY_REGION", "unknown"),
            api_key=env.get("AZURE_FOUNDRY_API_KEY"),
            # Explicit opt-in required — API keys are a fallback, never the default (spec 2.4).
            use_api_key_fallback=env.get("AZURE_FOUNDRY_USE_API_KEY", "false").strip().lower() == "true",
        )

    def require_azure_monitor_config(self) -> None:
        missing = [
            name
            for name, value in [
                ("AZURE_SUBSCRIPTION_ID", self.subscription_id),
                ("AZURE_RESOURCE_GROUP", self.resource_group),
                ("AZURE_FOUNDRY_RESOURCE_NAME", self.foundry_resource_name),
            ]
            if not value
        ]
        if missing:
            raise ConfigurationError(
                f"Azure Monitor reconciliation needs {missing} set — these identify the Foundry "
                f"resource whose metrics to query. Set them or skip reconciliation with --no-azure-monitor."
            )


def default_run_id() -> str:
    """A UTC-timestamp run ID, used when BENCHMARK_RUN_ID isn't set.
    Public (not resolved through EnvironmentSettings.from_env()) so
    commands like `dry-run` and `validate-config` can generate one
    without requiring AZURE_FOUNDRY_ENDPOINT to already be configured.
    """
    import datetime as _dt

    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%d-%H%M%S")


# ---------------------------------------------------------------------------
# Model configuration
# ---------------------------------------------------------------------------


def load_model_configs(path: Path) -> list[ModelConfig]:
    """Loads and validates config/models.yaml.

    Raises ConfigurationError for a missing file, a malformed entry, a
    duplicate logical_name/deployment_name, or zero enabled models —
    every one of these is a configuration mistake worth failing fast
    on, before any network call is attempted.
    """
    if not path.exists():
        raise ConfigurationError(f"Model config file not found: {path}")
    with path.open("r", encoding="utf-8") as handle:
        raw = yaml.safe_load(handle) or {}
    raw_models = raw.get("models") or []
    if not raw_models:
        raise ConfigurationError(f"{path} has no entries under 'models'.")

    configs = [ModelConfig.from_dict(entry) for entry in raw_models]

    seen_logical: set[str] = set()
    seen_deployment: set[str] = set()
    for config in configs:
        if config.logical_name in seen_logical:
            raise ConfigurationError(f"Duplicate logical_name in {path}: {config.logical_name!r}")
        if config.deployment_name in seen_deployment:
            raise ConfigurationError(f"Duplicate deployment_name in {path}: {config.deployment_name!r}")
        seen_logical.add(config.logical_name)
        seen_deployment.add(config.deployment_name)

    enabled = [config for config in configs if config.enabled]
    if not enabled:
        raise ConfigurationError(f"Every model entry in {path} has enabled: false — nothing to benchmark.")

    return configs


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------


@dataclasses.dataclass
class ResolvedAuth:
    """The credential to use for every backend, resolved once per run."""

    mode: str  # "entra_id" | "api_key"
    token_credential: Optional[TokenCredential] = None
    api_key: Optional[str] = None


def resolve_auth(settings: EnvironmentSettings) -> ResolvedAuth:
    """Resolves authentication per spec 2.4.

    DefaultAzureCredential is preferred and covers both managed
    identity (when running in Azure) and Azure CLI credentials (for
    local development) internally — it tries a chain of credential
    sources in order and uses the first one that works, so this
    function doesn't need to special-case "am I in Azure?" itself.

    API keys are used only when AZURE_FOUNDRY_USE_API_KEY=true is set
    explicitly (an opt-in fallback, never the default) and
    AZURE_FOUNDRY_API_KEY is present.
    """
    if settings.use_api_key_fallback:
        if not settings.api_key:
            raise ConfigurationError(
                "AZURE_FOUNDRY_USE_API_KEY=true but AZURE_FOUNDRY_API_KEY is not set."
            )
        return ResolvedAuth(mode="api_key", api_key=settings.api_key)

    from azure.identity import DefaultAzureCredential

    credential = DefaultAzureCredential(exclude_interactive_browser_credential=True)
    return ResolvedAuth(mode="entra_id", token_credential=credential)


# ---------------------------------------------------------------------------
# Per-deployment client construction
# ---------------------------------------------------------------------------


@dataclasses.dataclass
class ModelClient:
    """A configured, ready-to-call client for one model deployment."""

    config: ModelConfig
    backend: str  # "azure-ai-inference" | "azure-openai"
    client: object  # ChatCompletionsClient | openai.AzureOpenAI


def build_model_client(config: ModelConfig, settings: EnvironmentSettings, auth: ResolvedAuth) -> ModelClient:
    """Builds the SDK client for one model entry. No network call is made
    here — construction is always lazy (the same pattern the sibling
    Foundry-Workshop labs use for FoundryChatClient/GitHubCopilotAgent).
    """
    if config.provider == "azure-openai":
        client = _build_azure_openai_client(settings, auth)
        return ModelClient(config=config, backend="azure-openai", client=client)
    if config.provider == "deepseek":
        client = _build_inference_client(settings, auth)
        return ModelClient(config=config, backend="azure-ai-inference", client=client)
    raise ConfigurationError(f"Unhandled provider {config.provider!r} for {config.logical_name!r}")


def _build_azure_openai_client(settings: EnvironmentSettings, auth: ResolvedAuth):
    from openai import AzureOpenAI

    if auth.mode == "api_key":
        return AzureOpenAI(azure_endpoint=settings.foundry_endpoint, api_version=settings.api_version, api_key=auth.api_key)
    from azure.identity import get_bearer_token_provider

    token_provider = get_bearer_token_provider(auth.token_credential, _COGNITIVE_SERVICES_SCOPE)
    return AzureOpenAI(
        azure_endpoint=settings.foundry_endpoint,
        api_version=settings.api_version,
        azure_ad_token_provider=token_provider,
    )


def _build_inference_client(settings: EnvironmentSettings, auth: ResolvedAuth):
    from azure.ai.inference import ChatCompletionsClient

    credential: Union[AzureKeyCredential, TokenCredential]
    credential = AzureKeyCredential(auth.api_key) if auth.mode == "api_key" else auth.token_credential
    return ChatCompletionsClient(
        endpoint=settings.foundry_endpoint,
        credential=credential,
        api_version=settings.api_version,
    )


def build_model_clients(
    configs: list[ModelConfig], settings: EnvironmentSettings, auth: ResolvedAuth
) -> dict[str, ModelClient]:
    """Builds a client for every *enabled* model config, keyed by logical_name."""
    return {config.logical_name: build_model_client(config, settings, auth) for config in configs if config.enabled}


def validate_deployment_live(model_client: ModelClient) -> None:
    """Makes one minimal real request to confirm the deployment resolves.

    Not called from unit tests (it always hits the network) — the CLI's
    `validate-config` and `dry-run` commands call this explicitly, and
    the benchmark runner's warm-up phase provides the same signal for a
    normal run. Wraps any SDK error into DeploymentResolutionError so
    the failure names the deployment instead of surfacing a raw
    traceback.
    """
    try:
        if model_client.backend == "azure-openai":
            model_client.client.chat.completions.create(
                model=model_client.config.deployment_name,
                messages=[{"role": "user", "content": "ping"}],
                max_completion_tokens=1,
            )
        else:
            model_client.client.complete(
                model=model_client.config.deployment_name,
                messages=[{"role": "user", "content": "ping"}],
                max_tokens=1,
            )
    except Exception as exc:  # noqa: BLE001 - deliberately broad, re-raised as a typed error
        raise DeploymentResolutionError(
            logical_name=model_client.config.logical_name,
            deployment_name=model_client.config.deployment_name,
            provider=model_client.config.provider,
            detail=str(exc),
        ) from exc
