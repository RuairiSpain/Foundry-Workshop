"""Swaps MAF's own harness (Lab 21) for the GitHub Copilot SDK's agent,
on a store-ops agent that proposes config-file edits for a human to
approve before anything is written.
"""

from __future__ import annotations

import dataclasses
from pathlib import Path

from agent_framework.github import GitHubCopilotAgent

STORE_OPS_INSTRUCTIONS = (
    "You edit Cascadia store-ops config files. Propose changes; never write "
    "a file directly. A human approves every change before it's applied."
)


def build_store_ops_agent() -> GitHubCopilotAgent:
    """Builds the store-ops agent on the GitHub Copilot harness instead of MAF's own."""
    # TODO(lab-23): return a GitHubCopilotAgent built from
    # STORE_OPS_INSTRUCTIONS, with name="cascadia-store-ops".
    raise NotImplementedError("build_store_ops_agent is not implemented yet")


@dataclasses.dataclass
class ConfigEditProposal:
    file_path: Path
    original_content: str
    proposed_content: str

    @property
    def diff_preview(self) -> str:
        """A minimal preview a human reviews before approving."""
        return f"- {self.original_content}\n+ {self.proposed_content}"


def propose_config_edit(file_path: Path, *, new_value: str) -> ConfigEditProposal:
    """Reads the current file and proposes a replacement. Never writes."""
    # TODO(lab-23): read file_path's current text if it exists, otherwise
    # use "", and return a ConfigEditProposal.
    raise NotImplementedError("propose_config_edit is not implemented yet")


def apply_config_edit(proposal: ConfigEditProposal, *, approved: bool) -> str:
    """Writes the proposed content only if a human approved it."""
    # TODO(lab-23): raise PermissionError if not approved. Otherwise
    # write proposal.proposed_content to proposal.file_path and return a
    # confirmation string.
    raise NotImplementedError("apply_config_edit is not implemented yet")


def main() -> None:
    config_path = (
        Path(__file__).resolve().parents[3] / "case-study" / "store-ops-configs" / "store-hours.yaml"
    )
    proposal = propose_config_edit(config_path, new_value=config_path.read_text() + "\n# reviewed\n")
    print(proposal.diff_preview)
    approved = input("Approve this edit? [y/N] ").strip().lower() == "y"
    print(apply_config_edit(proposal, approved=approved))


if __name__ == "__main__":
    main()
