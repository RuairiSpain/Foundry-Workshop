"""Uploads Cascadia's policy documents, builds a vector store from them,
and compares a grounded answer against an ungrounded one on the same
question.

Verified against `azure-ai-agents` 1.1.0: file upload and vector store
creation are `AgentsClient.files.upload()` and
`AgentsClient.vector_stores.create()` — nested under the agents client,
not `AIProjectClient.files`/`.vector_stores`. `ask_grounded()`'s
`tools=`/`tool_resources=` on a bare chat completion is a simplified
illustration of the *concept*, not a literal endpoint: the real
mechanism for attaching a vector store to an answer is the Agents API's
`file_search` tool on an agent (Lab 09), which this lab — Module 2,
before agents exist in the curriculum — can't introduce yet.
"""

from __future__ import annotations

import dataclasses

CASE_STUDY_DOCS = ["case-study/return-policy.md", "case-study/store-manual.md"]


def upload_documents(files_client, file_paths: list[str]) -> list:
    """Uploads each file and returns the resulting file objects, in order."""
    return [files_client.upload(file_path=path) for path in file_paths]


def build_knowledge_base(vector_stores_client, uploaded_files: list, *, name: str):
    """Creates a vector store from already-uploaded files."""
    file_ids = [file.id for file in uploaded_files]
    return vector_stores_client.create(name=name, file_ids=file_ids)


def _file_search_tool_resources(vector_store_id: str) -> dict:
    return {"file_search": {"vector_store_ids": [vector_store_id]}}


def ask_grounded(chat_client, question: str, *, deployment_name: str, vector_store_id: str) -> str:
    """Asks a question with the knowledge base attached as a tool resource."""
    response = chat_client.chat.completions.create(
        model=deployment_name,
        messages=[{"role": "user", "content": question}],
        tools=[{"type": "file_search"}],
        tool_resources=_file_search_tool_resources(vector_store_id),
    )
    return response.choices[0].message.content


def ask_ungrounded(chat_client, question: str, *, deployment_name: str) -> str:
    """Asks the same question with no knowledge base attached."""
    response = chat_client.chat.completions.create(
        model=deployment_name,
        messages=[{"role": "user", "content": question}],
    )
    return response.choices[0].message.content


@dataclasses.dataclass
class GroundingComparison:
    grounded_answer: str
    ungrounded_answer: str


def compare_grounding(chat_client, question: str, *, deployment_name: str, vector_store_id: str) -> GroundingComparison:
    """Asks the same question grounded and ungrounded, for side-by-side reading."""
    grounded = ask_grounded(chat_client, question, deployment_name=deployment_name, vector_store_id=vector_store_id)
    ungrounded = ask_ungrounded(chat_client, question, deployment_name=deployment_name)
    return GroundingComparison(grounded_answer=grounded, ungrounded_answer=ungrounded)


def main() -> None:  # pragma: no cover - real SDK wiring and CLI entry point, exercised manually
    import os

    from azure.ai.agents import AgentsClient
    from azure.ai.projects import AIProjectClient
    from azure.identity import DefaultAzureCredential

    endpoint = os.environ["FOUNDRY_PROJECT_ENDPOINT"]
    client = AIProjectClient(endpoint=endpoint, credential=DefaultAzureCredential())
    agents_client = AgentsClient(endpoint=endpoint, credential=DefaultAzureCredential())

    uploaded = upload_documents(agents_client.files, CASE_STUDY_DOCS)
    vector_store = build_knowledge_base(agents_client.vector_stores, uploaded, name="cascadia-policy-kb")

    chat_client = client.get_openai_client()
    deployment_name = os.environ.get("LOW_COST_DEPLOYMENT", "cascadia-low-cost")
    question = "Can I return a carabiner I already took out of its packaging?"

    comparison = compare_grounding(
        chat_client, question, deployment_name=deployment_name, vector_store_id=vector_store.id
    )
    print(f"Grounded:   {comparison.grounded_answer}")
    print(f"Ungrounded: {comparison.ungrounded_answer}")


if __name__ == "__main__":  # pragma: no cover
    main()
