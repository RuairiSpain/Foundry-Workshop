"""Uploads Cascadia's policy documents, builds a vector store from them,
and compares a grounded answer against an ungrounded one on the same
question.
"""

from __future__ import annotations

import dataclasses

CASE_STUDY_DOCS = ["case-study/return-policy.md", "case-study/store-manual.md"]


def upload_documents(files_client, file_paths: list[str]) -> list:
    """Uploads each file and returns the resulting file objects, in order."""
    # TODO(lab-06): call files_client.upload(file_path=...) once per path.
    raise NotImplementedError("upload_documents is not implemented yet")


def build_knowledge_base(vector_stores_client, uploaded_files: list, *, name: str):
    """Creates a vector store from already-uploaded files."""
    # TODO(lab-06): collect the .id of each uploaded file, then call
    # vector_stores_client.create(name=name, file_ids=file_ids).
    raise NotImplementedError("build_knowledge_base is not implemented yet")


def _file_search_tool_resources(vector_store_id: str) -> dict:
    return {"file_search": {"vector_store_ids": [vector_store_id]}}


def ask_grounded(chat_client, question: str, *, deployment_name: str, vector_store_id: str) -> str:
    """Asks a question with the knowledge base attached as a tool resource."""
    # TODO(lab-06): call chat_client.complete() with model, a one-message
    # conversation, tools=[{"type": "file_search"}], and
    # tool_resources=_file_search_tool_resources(vector_store_id).
    raise NotImplementedError("ask_grounded is not implemented yet")


def ask_ungrounded(chat_client, question: str, *, deployment_name: str) -> str:
    """Asks the same question with no knowledge base attached."""
    # TODO(lab-06): call chat_client.complete() with model and a
    # one-message conversation, and nothing else.
    raise NotImplementedError("ask_ungrounded is not implemented yet")


@dataclasses.dataclass
class GroundingComparison:
    grounded_answer: str
    ungrounded_answer: str


def compare_grounding(chat_client, question: str, *, deployment_name: str, vector_store_id: str) -> GroundingComparison:
    """Asks the same question grounded and ungrounded, for side-by-side reading."""
    # TODO(lab-06): call ask_grounded() and ask_ungrounded(), and return
    # a GroundingComparison built from both answers.
    raise NotImplementedError("compare_grounding is not implemented yet")


def main() -> None:
    import os

    from azure.ai.projects import AIProjectClient
    from azure.identity import DefaultAzureCredential

    endpoint = os.environ["FOUNDRY_PROJECT_ENDPOINT"]
    client = AIProjectClient(endpoint=endpoint, credential=DefaultAzureCredential())

    uploaded = upload_documents(client.files, CASE_STUDY_DOCS)
    vector_store = build_knowledge_base(client.vector_stores, uploaded, name="cascadia-policy-kb")

    chat_client = client.inference.get_chat_completions_client()
    deployment_name = os.environ.get("LOW_COST_DEPLOYMENT", "cascadia-low-cost")
    question = "Can I return a carabiner I already took out of its packaging?"

    comparison = compare_grounding(
        chat_client, question, deployment_name=deployment_name, vector_store_id=vector_store.id
    )
    print(f"Grounded:   {comparison.grounded_answer}")
    print(f"Ungrounded: {comparison.ungrounded_answer}")


if __name__ == "__main__":
    main()
