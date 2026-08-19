"""CLI command building and output parsing for provision_project.ipynb.

Split out from the notebook so this logic is unit-testable: a notebook
cell can't be imported by pytest, but a plain function can. The notebook
imports this module and calls into it.
"""

from __future__ import annotations

import json
import subprocess


def build_project_create_command(*, account_name: str, resource_group: str, attendee_id: str) -> list[str]:
    """Builds the az CLI command that creates one attendee's project.

    No `account create` step here — unlike Lab 01's per-workshop hub
    setup, this command only ever targets the hub the instructor already
    created.
    """
    # TODO(lab-02): return the argument list for:
    #   az cognitiveservices account project create \
    #     --account-name <account_name> --resource-group <resource_group> \
    #     --name proj-<attendee_id> --output json
    raise NotImplementedError("build_project_create_command is not implemented yet")


def build_project_show_command(*, account_name: str, resource_group: str, attendee_id: str) -> list[str]:
    """Builds the az CLI command that reads back a project's details."""
    return [
        "az",
        "cognitiveservices",
        "account",
        "project",
        "show",
        "--account-name",
        account_name,
        "--resource-group",
        resource_group,
        "--name",
        f"proj-{attendee_id}",
        "--output",
        "json",
    ]


def parse_project_endpoint(cli_output_json: str) -> str:
    """Extracts the project endpoint from `az ... project show` output.

    Raises KeyError with the raw payload attached if the expected field
    is missing.
    """
    # TODO(lab-02): parse cli_output_json and return payload["properties"]["endpoint"].
    # Catch KeyError and re-raise it with the raw payload in the message,
    # using `raise ... from exc`.
    raise NotImplementedError("parse_project_endpoint is not implemented yet")


def run_az_command(cmd: list[str]) -> subprocess.CompletedProcess:
    """Runs an az CLI command and returns the completed process."""
    return subprocess.run(cmd, capture_output=True, text=True, check=True)
