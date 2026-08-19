"""Tests for solution/foundry_iq.py.

main() is excluded from coverage — real SDK wiring and a CLI entry
point, exercised manually, not under test.
"""

from solution.foundry_iq import (
    ask_file_search,
    ask_knowledge_base,
    build_sources,
    compare_retrieval,
    create_knowledge_base,
    upload_documents,
)
from testing.foundry_mocks import FakeChatCompletionsClient, FakeFilesClient, FakeKnowledgeBasesClient


def test_build_sources_combines_file_and_structured_sources():
    files_client = FakeFilesClient()
    uploaded = upload_documents(files_client, ["a.md", "b.md"])

    sources = build_sources(uploaded, ["catalog.csv"])

    assert sources == [
        {"type": "file", "file_id": uploaded[0].id},
        {"type": "file", "file_id": uploaded[1].id},
        {"type": "structured", "path": "catalog.csv"},
    ]


def test_create_knowledge_base_stores_all_sources():
    knowledge_bases_client = FakeKnowledgeBasesClient()
    sources = [{"type": "structured", "path": "catalog.csv"}]

    kb = create_knowledge_base(knowledge_bases_client, sources, name="cascadia-foundry-iq")

    assert kb.name == "cascadia-foundry-iq"
    assert kb.sources == sources


def test_ask_knowledge_base_attaches_the_knowledge_base_tool():
    chat_client = FakeChatCompletionsClient()
    chat_client.queue_reply("The tent is $189 and yes, returnable within 60 days.")

    answer = ask_knowledge_base(
        chat_client, "question", deployment_name="cascadia-low-cost", knowledge_base_id="kb-0001"
    )

    assert answer == "The tent is $189 and yes, returnable within 60 days."
    call = chat_client.calls[0]
    assert call["tools"] == [{"type": "knowledge_base"}]
    assert call["tool_resources"] == {"knowledge_base": {"knowledge_base_id": "kb-0001"}}


def test_ask_file_search_attaches_the_file_search_tool_not_knowledge_base():
    chat_client = FakeChatCompletionsClient()
    chat_client.queue_reply("Returnable within 60 days. Price not in these documents.")

    ask_file_search(chat_client, "question", deployment_name="cascadia-low-cost", vector_store_id="vs-0001")

    call = chat_client.calls[0]
    assert call["tools"] == [{"type": "file_search"}]


def test_compare_retrieval_shows_foundry_iq_answers_the_price_part_too():
    chat_client = FakeChatCompletionsClient()
    chat_client.queue_reply("It's returnable within 60 days. I don't have pricing information.")
    chat_client.queue_reply("The tent is $189.00 and returnable within 60 days.")

    comparison = compare_retrieval(
        chat_client,
        "What's the tent's price, and can I return it in 60 days?",
        deployment_name="cascadia-low-cost",
        vector_store_id="vs-0001",
        knowledge_base_id="kb-0001",
    )

    assert "$189" not in comparison.file_search_answer
    assert "$189" in comparison.foundry_iq_answer
