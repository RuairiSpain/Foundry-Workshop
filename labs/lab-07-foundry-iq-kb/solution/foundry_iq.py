"""Builds a Foundry IQ knowledge base spanning the product catalog and
Cascadia's policy documents, then asks a question that only a
multi-source knowledge base can answer in full — Lab 06's single-source
file search can only ground half of it.

Verified against `azure-ai-agents` 1.1.0 for file upload and vector
stores: `AgentsClient.files.upload()` and
`AgentsClient.vector_stores.create()`, nested under the agents client,
not `AIProjectClient`. Foundry IQ knowledge bases have no stable typed
SDK as of writing this workshop — a real call goes through
`AIProjectClient.send_request()` against a preview REST surface; see
`create_knowledge_base()`'s caller in main() for the caveat.
"""

from __future__ import annotations

import dataclasses

CASE_STUDY_DOCS = ["case-study/return-policy.md", "case-study/store-manual.md"]
CASE_STUDY_STRUCTURED = ["case-study/product-catalog.csv"]


def upload_documents(files_client, file_paths: list[str]) -> list:
    """Uploads each file and returns the resulting file objects, in order."""
    return [files_client.upload(file_path=path) for path in file_paths]


def build_sources(uploaded_files: list, structured_paths: list[str]) -> list[dict]:
    """Describes every source Foundry IQ should unify: uploaded files and
    structured data it reads directly, without a separate upload step.
    """
    file_sources = [{"type": "file", "file_id": file.id} for file in uploaded_files]
    structured_sources = [{"type": "structured", "path": path} for path in structured_paths]
    return file_sources + structured_sources


def create_knowledge_base(knowledge_bases_client, sources: list[dict], *, name: str):
    return knowledge_bases_client.create(name=name, sources=sources)


def _knowledge_base_tool_resources(knowledge_base_id: str) -> dict:
    return {"knowledge_base": {"knowledge_base_id": knowledge_base_id}}


def ask_knowledge_base(chat_client, question: str, *, deployment_name: str, knowledge_base_id: str) -> str:
    """Asks a question grounded in the Foundry IQ knowledge base."""
    response = chat_client.chat.completions.create(
        model=deployment_name,
        messages=[{"role": "user", "content": question}],
        tools=[{"type": "knowledge_base"}],
        tool_resources=_knowledge_base_tool_resources(knowledge_base_id),
    )
    return response.choices[0].message.content


def ask_file_search(chat_client, question: str, *, deployment_name: str, vector_store_id: str) -> str:
    """Asks the same question through Lab 06's single-source file search,
    for comparison.
    """
    response = chat_client.chat.completions.create(
        model=deployment_name,
        messages=[{"role": "user", "content": question}],
        tools=[{"type": "file_search"}],
        tool_resources={"file_search": {"vector_store_ids": [vector_store_id]}},
    )
    return response.choices[0].message.content


@dataclasses.dataclass
class RetrievalComparison:
    file_search_answer: str
    foundry_iq_answer: str


def compare_retrieval(
    chat_client, question: str, *, deployment_name: str, vector_store_id: str, knowledge_base_id: str
) -> RetrievalComparison:
    """Compares a single-source file-search answer against a multi-source
    Foundry IQ answer, on the same question.
    """
    file_search_answer = ask_file_search(
        chat_client, question, deployment_name=deployment_name, vector_store_id=vector_store_id
    )
    foundry_iq_answer = ask_knowledge_base(
        chat_client, question, deployment_name=deployment_name, knowledge_base_id=knowledge_base_id
    )
    return RetrievalComparison(file_search_answer=file_search_answer, foundry_iq_answer=foundry_iq_answer)


def main() -> None:  # pragma: no cover - real SDK wiring and CLI entry point, exercised manually
    import os

    from azure.ai.agents import AgentsClient
    from azure.ai.projects import AIProjectClient
    from azure.identity import DefaultAzureCredential

    endpoint = os.environ["FOUNDRY_PROJECT_ENDPOINT"]
    # Foundry IQ knowledge bases have no stable typed SDK as of writing
    # this workshop — client.knowledge_bases below is this lab's own
    # stand-in for AIProjectClient.send_request() against a preview
    # REST surface, the same one foundry_mocks.py's
    # FakeKnowledgeBasesClient models for tests.
    client = AIProjectClient(endpoint=endpoint, credential=DefaultAzureCredential(), allow_preview=True)
    agents_client = AgentsClient(endpoint=endpoint, credential=DefaultAzureCredential())

    uploaded = upload_documents(agents_client.files, CASE_STUDY_DOCS)
    sources = build_sources(uploaded, CASE_STUDY_STRUCTURED)
    knowledge_base = create_knowledge_base(client.knowledge_bases, sources, name="cascadia-foundry-iq")

    # A vector store over the same two files, so the comparison is fair —
    # both sides ground on the policy docs; only Foundry IQ also has the
    # catalog.
    vector_store = agents_client.vector_stores.create(name="cascadia-policy-kb", file_ids=[f.id for f in uploaded])

    chat_client = client.get_openai_client()
    deployment_name = os.environ.get("LOW_COST_DEPLOYMENT", "cascadia-low-cost")
    question = (
        "What's the price of the 2-person trail tent, and can I return it "
        "within 60 days if it doesn't fit my pack?"
    )

    comparison = compare_retrieval(
        chat_client,
        question,
        deployment_name=deployment_name,
        vector_store_id=vector_store.id,
        knowledge_base_id=knowledge_base.id,
    )
    print(f"File search: {comparison.file_search_answer}")
    print(f"Foundry IQ:  {comparison.foundry_iq_answer}")


if __name__ == "__main__":  # pragma: no cover
    main()
