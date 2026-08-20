"""Tests for solution/knowledge_base.py.

main() is excluded from coverage — real SDK wiring and a CLI entry
point, exercised manually, not under test.
"""

from solution.knowledge_base import (
    ask_grounded,
    ask_ungrounded,
    build_knowledge_base,
    compare_grounding,
    upload_documents,
)
from testing.foundry_mocks import FakeAgentFilesClient, FakeAgentVectorStoresClient, FakeOpenAIClient


def test_upload_documents_uploads_each_path_in_order():
    files_client = FakeAgentFilesClient()

    uploaded = upload_documents(files_client, ["a.md", "b.md"])

    assert [f.filename for f in uploaded] == ["a.md", "b.md"]


def test_build_knowledge_base_uses_the_uploaded_file_ids():
    files_client = FakeAgentFilesClient()
    vector_stores_client = FakeAgentVectorStoresClient()
    uploaded = upload_documents(files_client, ["a.md", "b.md"])

    store = build_knowledge_base(vector_stores_client, uploaded, name="cascadia-policy-kb")

    assert store.name == "cascadia-policy-kb"
    assert store.file_ids == [uploaded[0].id, uploaded[1].id]


def test_ask_grounded_attaches_file_search_with_the_vector_store():
    chat_client = FakeOpenAIClient()
    chat_client.queue_reply("Grounded answer.")

    answer = ask_grounded(chat_client, "question", deployment_name="cascadia-low-cost", vector_store_id="vs-0001")

    assert answer == "Grounded answer."
    call = chat_client.calls[0]
    assert call["tools"] == [{"type": "file_search"}]
    assert call["tool_resources"] == {"file_search": {"vector_store_ids": ["vs-0001"]}}


def test_ask_ungrounded_sends_no_tools():
    chat_client = FakeOpenAIClient()
    chat_client.queue_reply("Ungrounded answer.")

    answer = ask_ungrounded(chat_client, "question", deployment_name="cascadia-low-cost")

    assert answer == "Ungrounded answer."
    assert "tools" not in chat_client.calls[0]
    assert "tool_resources" not in chat_client.calls[0]


def test_compare_grounding_returns_both_answers():
    chat_client = FakeOpenAIClient()
    chat_client.queue_reply("Grounded: no, protection is non-returnable once opened.")
    chat_client.queue_reply("Ungrounded: check the return policy for details.")

    comparison = compare_grounding(
        chat_client, "Can I return an opened carabiner?", deployment_name="cascadia-low-cost", vector_store_id="vs-0001"
    )

    assert comparison.grounded_answer.startswith("Grounded:")
    assert comparison.ungrounded_answer.startswith("Ungrounded:")
    assert len(chat_client.calls) == 2
