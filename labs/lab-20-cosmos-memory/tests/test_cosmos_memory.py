"""Tests for solution/cosmos_memory.py.

main() is excluded from coverage — real Cosmos SDK wiring and a CLI
entry point, exercised manually, not under test.
"""

import pytest

from solution.cosmos_memory import (
    build_memory_document,
    distill_profile,
    search_memory_by_customer,
    store_turn,
)
from testing.cosmos_mocks import FakeCosmosContainer


def test_build_memory_document_uses_thread_id_as_the_partition_key():
    document = build_memory_document(
        thread_id="thread-001", role="user", content="Hello", customer_email="maya@example.com"
    )

    assert document["threadId"] == "thread-001"
    assert document["customerEmail"] == "maya@example.com"
    assert document["role"] == "user"
    assert document["content"] == "Hello"
    assert document["id"]  # a UUID string, non-empty


def test_store_turn_writes_to_the_container():
    container = FakeCosmosContainer()

    store_turn(container, thread_id="thread-001", role="user", content="Hello", customer_email="maya@example.com")

    assert len(container.query_items()) == 1


def test_search_memory_by_customer_filters_to_one_customer():
    container = FakeCosmosContainer()
    store_turn(container, thread_id="t1", role="user", content="Hi", customer_email="maya@example.com")
    store_turn(container, thread_id="t2", role="user", content="Hi", customer_email="priya@example.com")

    results = search_memory_by_customer(container, customer_email="maya@example.com")

    assert len(results) == 1
    assert results[0]["customerEmail"] == "maya@example.com"


def test_distill_profile_collects_skus_mentioned_across_turns():
    turns = [
        {"customerEmail": "maya@example.com", "content": "I'm eyeing the TENT-2P-GRN."},
        {"customerEmail": "maya@example.com", "content": "Also the PACK-45L-BLU looked nice."},
    ]

    profile = distill_profile(turns)

    assert profile.customer_email == "maya@example.com"
    assert profile.mentioned_skus == ["PACK-45L-BLU", "TENT-2P-GRN"]
    assert profile.turn_count == 2


def test_distill_profile_deduplicates_repeated_mentions():
    turns = [
        {"customerEmail": "maya@example.com", "content": "TENT-2P-GRN is nice."},
        {"customerEmail": "maya@example.com", "content": "Yes, TENT-2P-GRN, definitely."},
    ]

    profile = distill_profile(turns)

    assert profile.mentioned_skus == ["TENT-2P-GRN"]


def test_distill_profile_handles_turns_with_no_sku_mentions():
    turns = [{"customerEmail": "maya@example.com", "content": "What are your store hours?"}]

    profile = distill_profile(turns)

    assert profile.mentioned_skus == []
    assert profile.turn_count == 1


def test_distill_profile_raises_for_an_empty_turn_list():
    with pytest.raises(ValueError, match="zero turns"):
        distill_profile([])


def test_end_to_end_store_search_distill():
    container = FakeCosmosContainer()
    store_turn(
        container,
        thread_id="t1",
        role="user",
        content="I'm eyeing the TENT-2P-GRN for a trip next month.",
        customer_email="maya@example.com",
    )
    store_turn(
        container, thread_id="t2", role="user", content="What's your return window?", customer_email="maya@example.com"
    )

    turns = search_memory_by_customer(container, customer_email="maya@example.com")
    profile = distill_profile(turns)

    assert profile.turn_count == 2
    assert profile.mentioned_skus == ["TENT-2P-GRN"]
