"""Tests for solution/store_ops_agent.py.

main() is excluded from coverage — it calls the real Copilot SDK and
reads interactive input, exercised manually, not under test.

build_store_ops_agent() constructs a real GitHubCopilotAgent with no
network call — the same lazy-construction pattern Lab 12's
FoundryChatClient uses.
"""

import pytest

from solution.store_ops_agent import apply_config_edit, build_store_ops_agent, propose_config_edit


def test_build_store_ops_agent_has_the_expected_name():
    agent = build_store_ops_agent()

    assert agent.name == "cascadia-store-ops"


def test_build_store_ops_agent_instructions_require_approval():
    agent = build_store_ops_agent()

    content = agent.default_options["system_message"]["content"]
    assert "human approves" in content


def test_propose_config_edit_reads_the_existing_file(tmp_path):
    config_file = tmp_path / "store-hours.yaml"
    config_file.write_text("seattle-flagship:\n  weekday: 9am-8pm\n")

    proposal = propose_config_edit(config_file, new_value="seattle-flagship:\n  weekday: 10am-8pm\n")

    assert proposal.original_content == "seattle-flagship:\n  weekday: 9am-8pm\n"
    assert proposal.proposed_content == "seattle-flagship:\n  weekday: 10am-8pm\n"


def test_propose_config_edit_handles_a_file_that_does_not_exist_yet(tmp_path):
    config_file = tmp_path / "new-config.yaml"

    proposal = propose_config_edit(config_file, new_value="new: value\n")

    assert proposal.original_content == ""


def test_diff_preview_shows_both_versions(tmp_path):
    config_file = tmp_path / "store-hours.yaml"
    config_file.write_text("old\n")

    proposal = propose_config_edit(config_file, new_value="new\n")

    assert proposal.diff_preview == "- old\n\n+ new\n"


def test_apply_config_edit_writes_when_approved(tmp_path):
    config_file = tmp_path / "store-hours.yaml"
    config_file.write_text("old\n")
    proposal = propose_config_edit(config_file, new_value="new\n")

    apply_config_edit(proposal, approved=True)

    assert config_file.read_text() == "new\n"


def test_apply_config_edit_raises_and_does_not_write_when_not_approved(tmp_path):
    config_file = tmp_path / "store-hours.yaml"
    config_file.write_text("old\n")
    proposal = propose_config_edit(config_file, new_value="new\n")

    with pytest.raises(PermissionError, match="not approved"):
        apply_config_edit(proposal, approved=False)

    assert config_file.read_text() == "old\n"
