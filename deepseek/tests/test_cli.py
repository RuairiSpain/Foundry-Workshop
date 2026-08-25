"""CLI argument parsing and the network-free commands
(validate-config, dry-run). `run`/`reconcile` need real Azure
credentials and are covered by the live smoke tests, not here.
"""

from __future__ import annotations

import textwrap

from src.cli import main


def _write_project(tmp_path):
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / "models.yaml").write_text(
        textwrap.dedent(
            """
            models:
              - logical_name: deepseek-v4-flash
                deployment_name: deepseek-v4-flash-3107
                provider: deepseek
                pricing_key: deepseek-v4-flash
            """
        ),
        encoding="utf-8",
    )
    (config_dir / "pricing.yaml").write_text(
        textwrap.dedent(
            """
            pricing_version: "v1"
            entries:
              - provider: deepseek
                model: deepseek-v4-flash
                deployment_type: standard
                region: any
                input_price_per_million: 1.0
                cached_input_price_per_million: 0.5
                output_price_per_million: 2.0
                currency: USD
                effective_date: "2026-01-01"
                source: manual-placeholder
            """
        ),
        encoding="utf-8",
    )
    data_path = tmp_path / "prompts.jsonl"
    data_path.write_text('{"prompt_id":"P1","category":"c","difficulty":"simple","max_output_tokens":10,"prompt":"hi"}\n', encoding="utf-8")
    return config_dir, data_path


def test_validate_config_succeeds_on_a_valid_project(tmp_path):
    config_dir, data_path = _write_project(tmp_path)
    exit_code = main(["--config-dir", str(config_dir), "--data", str(data_path), "validate-config"])
    assert exit_code == 0


def test_validate_config_fails_on_missing_config_dir(tmp_path):
    exit_code = main(["--config-dir", str(tmp_path / "nope"), "--data", str(tmp_path / "nope.jsonl"), "validate-config"])
    assert exit_code == 1


def test_dry_run_reports_work_item_count(tmp_path, capsys):
    config_dir, data_path = _write_project(tmp_path)
    exit_code = main(["--config-dir", str(config_dir), "--data", str(data_path), "dry-run", "--repeats", "4", "--warm-up", "1"])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Total measured work items: 4" in captured.out  # 1 model * 1 prompt * 4 repeats


def test_dry_run_fails_with_unmatched_model_filter(tmp_path, capsys):
    config_dir, data_path = _write_project(tmp_path)
    exit_code = main(["--config-dir", str(config_dir), "--data", str(data_path), "dry-run", "--model", "does-not-exist"])
    captured = capsys.readouterr()
    assert exit_code == 1
    assert "does not match any enabled model" in captured.out


def test_dry_run_fails_with_unmatched_category_filter(tmp_path, capsys):
    config_dir, data_path = _write_project(tmp_path)
    exit_code = main(["--config-dir", str(config_dir), "--data", str(data_path), "dry-run", "--category", "nonexistent-category"])
    assert exit_code == 1


def test_no_network_calls_are_reachable_from_validate_config_or_dry_run(tmp_path, monkeypatch):
    """Guards against a future regression that makes validate-config or
    dry-run construct a real SDK client. Any attempted import of the
    network-touching client classes fails the test.
    """
    config_dir, data_path = _write_project(tmp_path)

    def _fail(*args, **kwargs):
        raise AssertionError("no client should be constructed during validate-config/dry-run")

    monkeypatch.setattr("src.client_factory.build_model_client", _fail)

    assert main(["--config-dir", str(config_dir), "--data", str(data_path), "validate-config"]) == 0
    assert main(["--config-dir", str(config_dir), "--data", str(data_path), "dry-run"]) == 0
