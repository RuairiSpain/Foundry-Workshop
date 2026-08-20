"""Swaps MAF's own harness (Lab 21) for the GitHub Copilot SDK's agent,
on a store-ops agent that proposes config-file edits for a human to
approve before anything is written.

Optional: requires GitHub Copilot SDK access alongside your Foundry
access. If you don't have it, read through this lab instead of running
it — Lab 21 already covered the harness concept this one specializes.
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
    return GitHubCopilotAgent(STORE_OPS_INSTRUCTIONS, name="cascadia-store-ops")


@dataclasses.dataclass
class ConfigEditProposal:
    file_path: Path
    original_content: str
    proposed_content: str

    @property
    def diff_preview(self) -> str:
        """A minimal preview a human reviews before approving.

        Real production code would use difflib for a proper unified
        diff; this keeps the review surface small and readable for the
        lab.
        """
        return f"- {self.original_content}\n+ {self.proposed_content}"


def propose_config_edit(file_path: Path, *, new_value: str) -> ConfigEditProposal:
    """Reads the current file and proposes a replacement. Never writes."""
    original = file_path.read_text() if file_path.exists() else ""
    return ConfigEditProposal(file_path=file_path, original_content=original, proposed_content=new_value)


def apply_config_edit(proposal: ConfigEditProposal, *, approved: bool) -> str:
    """Writes the proposed content only if a human approved it.

    Raises PermissionError instead of silently skipping an unapproved
    edit — a caller that forgets to check a return value here should
    fail loudly, not fail to notice that nothing was written.
    """
    if not approved:
        raise PermissionError(f"Edit to {proposal.file_path} was not approved")
    proposal.file_path.write_text(proposal.proposed_content)
    return f"Wrote {proposal.file_path}"


def main() -> None:  # pragma: no cover - real Copilot SDK call and CLI entry point, exercised manually
    config_path = (
        Path(__file__).resolve().parents[3] / "case-study" / "store-ops-configs" / "store-hours.yaml"
    )
    proposal = propose_config_edit(config_path, new_value=config_path.read_text() + "\n# reviewed\n")
    print(proposal.diff_preview)
    approved = input("Approve this edit? [y/N] ").strip().lower() == "y"
    print(apply_config_edit(proposal, approved=approved))


if __name__ == "__main__":  # pragma: no cover
    main()
