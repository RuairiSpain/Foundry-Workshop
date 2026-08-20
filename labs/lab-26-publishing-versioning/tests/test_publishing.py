"""Tests for solution/publishing.py.

main() is excluded from coverage — real SDK wiring and a CLI entry
point, exercised manually, not under test.
"""

import pytest

from solution.publishing import (
    canary_traffic_split,
    publish_first_version,
    publish_new_version,
    rollback_to_version,
)
from testing.foundry_mocks import FakeAgentApplicationsClient


def test_publish_first_version_creates_one_version_at_full_traffic():
    client = FakeAgentApplicationsClient()

    app = publish_first_version(client, name="cascadia-support-app", agent_id="agent-0001")

    assert len(app.versions) == 1
    assert app.traffic_split == {1: 100.0}


def test_publish_new_version_shifts_all_traffic_to_it_by_default():
    client = FakeAgentApplicationsClient()
    app = publish_first_version(client, name="cascadia-support-app", agent_id="agent-0001")

    version_2 = publish_new_version(client, app.id, agent_id="agent-0002", notes="Updated phrasing.")

    assert version_2.version == 2
    assert client.get(app.id).traffic_split == {2: 100.0}


def test_canary_traffic_split_splits_between_two_versions():
    client = FakeAgentApplicationsClient()
    app = publish_first_version(client, name="cascadia-support-app", agent_id="agent-0001")
    publish_new_version(client, app.id, agent_id="agent-0002", notes="v2")

    canary_traffic_split(client, app.id, stable_version=1, canary_version=2, canary_percent=10.0)

    assert client.get(app.id).traffic_split == {1: 90.0, 2: 10.0}


def test_canary_traffic_split_rejects_an_unknown_version():
    client = FakeAgentApplicationsClient()
    app = publish_first_version(client, name="cascadia-support-app", agent_id="agent-0001")

    with pytest.raises(ValueError, match="Unknown version"):
        canary_traffic_split(client, app.id, stable_version=1, canary_version=99, canary_percent=10.0)


def test_rollback_to_version_sends_it_full_traffic():
    client = FakeAgentApplicationsClient()
    app = publish_first_version(client, name="cascadia-support-app", agent_id="agent-0001")
    publish_new_version(client, app.id, agent_id="agent-0002", notes="v2")

    rollback_to_version(client, app.id, version=1)

    assert client.get(app.id).traffic_split == {1: 100.0}


def test_rollback_to_an_unknown_version_raises():
    client = FakeAgentApplicationsClient()
    app = publish_first_version(client, name="cascadia-support-app", agent_id="agent-0001")

    with pytest.raises(ValueError, match="Unknown version"):
        rollback_to_version(client, app.id, version=99)
