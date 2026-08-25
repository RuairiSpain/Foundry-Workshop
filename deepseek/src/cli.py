"""Command-line entry point.

    python -m src.cli validate-config
    python -m src.cli dry-run [filters...]
    python -m src.cli run [filters...] [--resume] [--azure-monitor]
    python -m src.cli reconcile --run-id <id>

Run from the `deepseek/` directory (or set PYTHONPATH to it) so the
default `config/`, `data/`, and `output/` paths resolve.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path
from typing import Optional

from . import aggregation, azure_monitor, benchmark_runner, telemetry
from .client_factory import (
    EnvironmentSettings,
    build_model_clients,
    default_run_id,
    load_model_configs,
    resolve_auth,
)
from .models import BenchmarkSettings, ConfigurationError, DeploymentResolutionError, PromptRecord
from .pricing import load_pricing_table


def load_prompts(path: Path) -> list[PromptRecord]:
    """Loads and validates data/prompts.jsonl.

    Raises ConfigurationError for a malformed line or a duplicate
    prompt_id — the same fail-fast posture as the YAML config loaders.
    """
    if not path.exists():
        raise ConfigurationError(f"Prompt dataset not found: {path}")
    prompts: list[PromptRecord] = []
    seen_ids: set[str] = set()
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ConfigurationError(f"{path}:{line_number} is not valid JSON: {exc}") from exc
            prompt = PromptRecord.from_dict(data)
            if prompt.prompt_id in seen_ids:
                raise ConfigurationError(f"{path}:{line_number} has a duplicate prompt_id: {prompt.prompt_id!r}")
            seen_ids.add(prompt.prompt_id)
            prompts.append(prompt)
    if not prompts:
        raise ConfigurationError(f"{path} contains no prompts.")
    return prompts


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="deepseek-benchmark", description=__doc__)
    parser.add_argument("--config-dir", type=Path, default=Path("config"))
    parser.add_argument("--data", type=Path, default=Path("data/prompts.jsonl"))
    parser.add_argument("--output-dir", type=Path, default=Path("output"))
    subparsers = parser.add_subparsers(dest="command", required=True)

    filters = argparse.ArgumentParser(add_help=False)
    filters.add_argument("--model", help="Restrict to one model's logical_name from models.yaml.")
    filters.add_argument("--category", help="Restrict to one prompt category.")
    filters.add_argument("--difficulty", help="Restrict to one prompt difficulty.")
    filters.add_argument("--repeats", type=int, default=5)
    filters.add_argument("--warm-up", type=int, default=3, dest="warm_up")
    filters.add_argument("--concurrency", type=int, default=1, help="1 = sequential latency test. >1 = throughput test.")
    filters.add_argument("--no-streaming", action="store_true")
    filters.add_argument("--temperature", type=float, default=0.0)
    filters.add_argument("--top-p", type=float, default=1.0, dest="top_p")
    filters.add_argument("--seed", type=int, default=42)
    filters.add_argument("--max-output-tokens", type=int, default=500, dest="max_output_tokens")
    filters.add_argument("--max-retries", type=int, default=3, dest="max_retries")
    filters.add_argument("--cooldown-min-ms", type=int, default=500, dest="cooldown_min_ms")
    filters.add_argument("--cooldown-max-ms", type=int, default=1000, dest="cooldown_max_ms")
    filters.add_argument("--no-randomize-model-order", action="store_true", dest="no_randomize_model_order")
    filters.add_argument("--no-randomize-prompt-order", action="store_true", dest="no_randomize_prompt_order")
    filters.add_argument("--run-id", help="Defaults to BENCHMARK_RUN_ID or a UTC timestamp.")

    subparsers.add_parser("validate-config", help="Load and validate config + prompts. No network calls.")
    subparsers.add_parser("dry-run", parents=[filters], help="Report what a run would do. No network calls.")

    run_parser = subparsers.add_parser("run", parents=[filters], help="Execute the benchmark.")
    run_parser.add_argument("--resume", action="store_true")
    run_parser.add_argument("--no-response-text", action="store_true", dest="no_response_text")
    run_parser.add_argument("--azure-monitor", action="store_true", help="Query Azure Monitor for reconciliation after the run.")

    reconcile_parser = subparsers.add_parser("reconcile", help="Reconcile an already-run benchmark against Azure Monitor.")
    reconcile_parser.add_argument("--run-id", required=True)
    reconcile_parser.add_argument("--window-padding-minutes", type=int, default=5)

    return parser


def settings_from_args(args: argparse.Namespace, *, run_id: str, store_response_text: bool) -> BenchmarkSettings:
    return BenchmarkSettings(
        run_id=run_id,
        warm_up_count=args.warm_up,
        repeats=args.repeats,
        concurrency=args.concurrency,
        streaming=not args.no_streaming,
        temperature=args.temperature,
        top_p=args.top_p,
        max_output_tokens_cap=args.max_output_tokens,
        seed=args.seed,
        cooldown_ms_min=args.cooldown_min_ms,
        cooldown_ms_max=args.cooldown_max_ms,
        max_retries=args.max_retries,
        randomize_model_order=not args.no_randomize_model_order,
        randomize_prompt_order=not args.no_randomize_prompt_order,
        store_response_text=store_response_text,
        model_filter=args.model,
        category_filter=args.category,
        difficulty_filter=args.difficulty,
    )


def cmd_validate_config(args: argparse.Namespace) -> int:
    try:
        model_configs = load_model_configs(args.config_dir / "models.yaml")
        pricing_version, pricing_entries = load_pricing_table(args.config_dir / "pricing.yaml")
        prompts = load_prompts(args.data)
    except ConfigurationError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 1
    enabled = [config for config in model_configs if config.enabled]
    print(f"models.yaml: {len(model_configs)} entries, {len(enabled)} enabled: {[c.logical_name for c in enabled]}")
    print(f"pricing.yaml: version {pricing_version!r}, {len(pricing_entries)} entries")
    print(f"prompts.jsonl: {len(prompts)} prompts, categories: {sorted({p.category for p in prompts})}")
    print("Configuration is valid.")
    return 0


def cmd_dry_run(args: argparse.Namespace) -> int:
    try:
        model_configs = load_model_configs(args.config_dir / "models.yaml")
        prompts = load_prompts(args.data)
    except ConfigurationError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 1
    import os

    run_id = args.run_id or os.environ.get("BENCHMARK_RUN_ID") or default_run_id()
    settings = settings_from_args(args, run_id=run_id, store_response_text=True)
    report = benchmark_runner.dry_run(model_configs, prompts, settings)
    print(f"Run ID: {report.run_id}")
    print(f"Models: {report.models}")
    print(f"Prompts matched: {report.total_prompts}, repeats: {report.repeats}, warm-up per model: {report.warm_up_per_model}")
    print(f"Total measured work items: {report.total_work_items}")
    print(f"Concurrency: {report.concurrency}, streaming: {report.streaming}, seed: {report.seed}")
    if report.errors:
        print("Errors:")
        for error in report.errors:
            print(f"  - {error}")
        return 1
    print("Dry run OK — no network calls were made.")
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    try:
        model_configs = load_model_configs(args.config_dir / "models.yaml")
        pricing_version, pricing_entries = load_pricing_table(args.config_dir / "pricing.yaml")
        prompts = load_prompts(args.data)
    except ConfigurationError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 1

    env_settings = EnvironmentSettings.from_env()
    run_id = args.run_id or env_settings.benchmark_run_id
    settings = settings_from_args(args, run_id=run_id, store_response_text=not args.no_response_text)

    telemetry.init_telemetry(env_settings.application_insights_connection_string)
    tracer = telemetry.get_tracer()

    try:
        auth = resolve_auth(env_settings)
        model_clients = build_model_clients(model_configs, env_settings, auth)
    except (ConfigurationError, DeploymentResolutionError) as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 1

    def on_record(record):
        attributes = telemetry.build_span_attributes(record, server_address=env_settings.foundry_endpoint)
        with telemetry.model_request_span(tracer, attributes):
            pass

    output_path = args.output_dir / "requests.jsonl"
    try:
        new_records = benchmark_runner.run(
            model_clients,
            model_configs,
            prompts,
            settings,
            region=env_settings.region,
            pricing_entries=pricing_entries,
            output_path=output_path,
            resume=args.resume,
            on_record=on_record,
        )
    except DeploymentResolutionError as exc:
        print(f"Deployment resolution error: {exc}", file=sys.stderr)
        return 1

    print(f"Run {run_id}: {len(new_records)} new request(s) written to {output_path}")

    all_records = benchmark_runner.load_records(output_path, run_id=run_id)
    summary_rows = aggregation.summarize(all_records)
    aggregation.write_model_summary_csv(summary_rows, args.output_dir / "model_summary.csv")
    aggregation.write_results_csv(all_records, args.output_dir / "results.csv")
    print(f"Wrote {args.output_dir / 'model_summary.csv'} ({len(summary_rows)} rows)")
    print(f"Wrote {args.output_dir / 'results.csv'} ({len(all_records)} rows)")

    if args.azure_monitor:
        return _run_reconciliation(args, env_settings, model_configs, all_records)
    return 0


def cmd_reconcile(args: argparse.Namespace) -> int:
    try:
        model_configs = load_model_configs(args.config_dir / "models.yaml")
    except ConfigurationError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 1
    env_settings = EnvironmentSettings.from_env()
    output_path = args.output_dir / "requests.jsonl"
    records = benchmark_runner.load_records(output_path, run_id=args.run_id)
    if not records:
        print(f"No records found for run_id {args.run_id!r} in {output_path}", file=sys.stderr)
        return 1
    return _run_reconciliation(args, env_settings, model_configs, records)


def _run_reconciliation(args: argparse.Namespace, env_settings: EnvironmentSettings, model_configs, records) -> int:
    try:
        env_settings.require_azure_monitor_config()
    except ConfigurationError as exc:
        print(f"Cannot reconcile: {exc}", file=sys.stderr)
        return 1

    padding_minutes = getattr(args, "window_padding_minutes", 5)
    start = min(dt.datetime.fromisoformat(r.started_at_utc) for r in records) - dt.timedelta(minutes=padding_minutes)
    end = max(dt.datetime.fromisoformat(r.completed_at_utc) for r in records) + dt.timedelta(minutes=padding_minutes)

    from .client_factory import resolve_auth

    auth = resolve_auth(env_settings)
    monitor_client = azure_monitor.build_monitor_client(auth.token_credential, env_settings.subscription_id)
    resource_id = azure_monitor.build_resource_id(
        subscription_id=env_settings.subscription_id,
        resource_group=env_settings.resource_group,
        foundry_resource_name=env_settings.foundry_resource_name,
    )

    all_reconciliation_rows = []
    for config in model_configs:
        if not config.enabled:
            continue
        model_records = [r for r in records if r.model == config.logical_name]
        if not model_records:
            continue
        sdk_input = sum(r.input_tokens or 0 for r in model_records)
        sdk_output = sum(r.output_tokens or 0 for r in model_records)

        if config.provider == "azure-openai":
            metric_names = list(azure_monitor.AZURE_OPENAI_METRIC_NAMES.keys())
        else:
            available = azure_monitor.list_available_metric_names(monitor_client, resource_id)
            metric_names = sorted(available)

        results = azure_monitor.query_metrics_for_window(
            monitor_client,
            resource_id,
            metric_names,
            start=start,
            end=end,
            deployment_dimension_filter=azure_monitor.deployment_filter(config.deployment_name),
        )
        all_reconciliation_rows.extend(
            aggregation.reconcile_tokens(
                model=config.logical_name,
                deployment_name=config.deployment_name,
                sdk_input_tokens=sdk_input,
                sdk_output_tokens=sdk_output,
                azure_monitor_results=results,
            )
        )

    aggregation.write_reconciliation_csv(all_reconciliation_rows, args.output_dir / "reconciliation.csv")
    print(f"Wrote {args.output_dir / 'reconciliation.csv'} ({len(all_reconciliation_rows)} rows)")
    return 0


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    handlers = {
        "validate-config": cmd_validate_config,
        "dry-run": cmd_dry_run,
        "run": cmd_run,
        "reconcile": cmd_reconcile,
    }
    return handlers[args.command](args)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
