"""Tests for solution/content_understanding.py.

main() is excluded from coverage — real SDK wiring and a CLI entry
point, exercised manually, not under test.
"""

import pytest

from solution.content_understanding import (
    RECEIPT_SCHEMA,
    add_receipt_to_knowledge_base,
    build_knowledge_base_source,
    extract_receipt_fields,
    validate_extraction,
)
from testing.foundry_mocks import FakeContentUnderstandingClient, FakeKnowledgeBasesClient


def test_extract_receipt_fields_calls_analyze_with_the_schema():
    client = FakeContentUnderstandingClient()
    client.script_result("receipt.txt", {"order_id": "CO-10231"})

    result = extract_receipt_fields(client, "receipt.txt")

    assert result == {"order_id": "CO-10231"}
    assert client.calls[0]["schema"] == RECEIPT_SCHEMA


def test_validate_extraction_passes_when_all_required_fields_are_present():
    result = validate_extraction(
        {"order_id": "CO-10231", "customer_email": "maya@example.com", "total_usd": 189.0}
    )

    assert result.is_complete is True
    assert result.missing_fields == []


def test_validate_extraction_flags_a_missing_field():
    result = validate_extraction({"order_id": "CO-10231", "total_usd": 189.0})

    assert result.is_complete is False
    assert result.missing_fields == ["customer_email"]


def test_validate_extraction_flags_an_empty_field_as_missing():
    result = validate_extraction({"order_id": "CO-10231", "customer_email": "", "total_usd": 189.0})

    assert "customer_email" in result.missing_fields


def test_build_knowledge_base_source_wraps_the_fields():
    source = build_knowledge_base_source({"order_id": "CO-10231"})

    assert source == {"type": "structured", "data": {"order_id": "CO-10231"}}


def test_add_receipt_to_knowledge_base_appends_the_source():
    knowledge_bases_client = FakeKnowledgeBasesClient()
    kb = knowledge_bases_client.create(name="cascadia-foundry-iq", sources=[])
    fields = {"order_id": "CO-10231", "customer_email": "maya@example.com", "total_usd": 189.0}

    updated_kb = add_receipt_to_knowledge_base(knowledge_bases_client, kb.id, fields)

    assert updated_kb.sources == [{"type": "structured", "data": fields}]


def test_add_receipt_to_knowledge_base_rejects_an_incomplete_extraction():
    knowledge_bases_client = FakeKnowledgeBasesClient()
    kb = knowledge_bases_client.create(name="cascadia-foundry-iq", sources=[])
    incomplete_fields = {"order_id": "CO-10231"}

    with pytest.raises(ValueError, match="customer_email"):
        add_receipt_to_knowledge_base(knowledge_bases_client, kb.id, incomplete_fields)

    assert kb.sources == []
