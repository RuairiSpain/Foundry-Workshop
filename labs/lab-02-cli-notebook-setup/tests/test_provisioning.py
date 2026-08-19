"""Tests for solution/provisioning.py.

run_az_command() is excluded from coverage — it's a real subprocess
call, exercised manually from the notebook, not under test.
"""

import json

import pytest

from solution.provisioning import (
    build_project_create_command,
    build_project_show_command,
    parse_project_endpoint,
)


def test_build_project_create_command_targets_project_create_not_account_create():
    cmd = build_project_create_command(
        account_name="cascadia-foundry-hub", resource_group="rg-cascadia-foundry-hub", attendee_id="07"
    )

    # The hub already exists — this command must be "account project
    # create", never "account create", or it'd try to build a second hub.
    assert cmd[:5] == ["az", "cognitiveservices", "account", "project", "create"]


def test_build_project_create_command_names_the_project_after_the_attendee():
    cmd = build_project_create_command(
        account_name="cascadia-foundry-hub", resource_group="rg-cascadia-foundry-hub", attendee_id="07"
    )

    name_index = cmd.index("--name") + 1
    assert cmd[name_index] == "proj-07"


def test_build_project_show_command_targets_the_same_project():
    cmd = build_project_show_command(
        account_name="cascadia-foundry-hub", resource_group="rg-cascadia-foundry-hub", attendee_id="07"
    )

    assert cmd[:5] == ["az", "cognitiveservices", "account", "project", "show"]
    name_index = cmd.index("--name") + 1
    assert cmd[name_index] == "proj-07"


def test_parse_project_endpoint_extracts_the_endpoint():
    output = json.dumps({"properties": {"endpoint": "https://proj-07.example.foundry.azure.com"}})

    endpoint = parse_project_endpoint(output)

    assert endpoint == "https://proj-07.example.foundry.azure.com"


def test_parse_project_endpoint_raises_with_the_payload_on_missing_field():
    output = json.dumps({"properties": {}})

    with pytest.raises(KeyError, match="properties"):
        parse_project_endpoint(output)
