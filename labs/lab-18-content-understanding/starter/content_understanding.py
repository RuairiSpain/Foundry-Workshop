"""Extracts structured fields from a receipt with Content Understanding,
validates the extraction, and feeds it into Lab 07's knowledge base as a
new source.

Verified against `azure-ai-contentunderstanding` 1.2.0b3's schema-based
field extraction. The real `ContentUnderstandingClient` is a
long-running-operation API (`begin_analyze()`, returning a poller) —
`content_understanding_client.analyze()` here simplifies that polling
loop to one synchronous call. Foundry IQ knowledge bases have no stable
typed SDK as of writing this workshop — see main() for that caveat.
"""

from __future__ import annotations

import dataclasses
from pathlib import Path

RECEIPT_SCHEMA = {
    "fields": {
        "order_id": {"type": "string"},
        "customer_email": {"type": "string"},
        "total_usd": {"type": "number"},
        "item_count": {"type": "integer"},
    }
}

REQUIRED_FIELDS = ["order_id", "customer_email", "total_usd"]


def extract_receipt_fields(content_understanding_client, file_path: Path, *, schema: dict = RECEIPT_SCHEMA) -> dict:
    """Calls Content Understanding to extract structured fields from one
    receipt, using `schema` to describe what to look for.
    """
    # TODO(lab-18): call content_understanding_client.analyze() with
    # file_path=str(file_path) and schema=schema, and return the result.
    raise NotImplementedError("extract_receipt_fields is not implemented yet")


@dataclasses.dataclass
class ValidationResult:
    missing_fields: list[str]

    @property
    def is_complete(self) -> bool:
        return not self.missing_fields


def validate_extraction(fields: dict, *, required_fields: list[str] = REQUIRED_FIELDS) -> ValidationResult:
    """Checks that every required field came back with a non-empty value."""
    # TODO(lab-18): build the list of required_fields whose value in
    # `fields` is missing or falsy, and return a ValidationResult.
    raise NotImplementedError("validate_extraction is not implemented yet")


def build_knowledge_base_source(extracted_fields: dict) -> dict:
    """Shapes an extraction result as a structured knowledge base source."""
    # TODO(lab-18): return {"type": "structured", "data": extracted_fields}.
    raise NotImplementedError("build_knowledge_base_source is not implemented yet")


def add_receipt_to_knowledge_base(knowledge_bases_client, knowledge_base_id: str, extracted_fields: dict) -> dict:
    """Adds one validated extraction to an existing knowledge base."""
    # TODO(lab-18): call validate_extraction(). If it's not complete,
    # raise ValueError naming the missing fields. Otherwise build a
    # source with build_knowledge_base_source() and call
    # knowledge_bases_client.add_source(knowledge_base_id, source).
    raise NotImplementedError("add_receipt_to_knowledge_base is not implemented yet")


def main() -> None:
    import os

    from azure.ai.projects import AIProjectClient
    from azure.identity import DefaultAzureCredential

    receipt_path = Path(__file__).resolve().parents[3] / "case-study" / "receipts-and-specs" / "receipt-CO-10231.txt"
    endpoint = os.environ["FOUNDRY_PROJECT_ENDPOINT"]
    knowledge_base_id = os.environ["FOUNDRY_IQ_KNOWLEDGE_BASE_ID"]
    # client.content_understanding and client.knowledge_bases are this
    # lab's own stand-ins: the real Content Understanding call is a
    # poller (see the module docstring), and knowledge bases have no
    # stable typed SDK yet — a real call goes through
    # AIProjectClient.send_request() against a preview REST surface.
    client = AIProjectClient(endpoint=endpoint, credential=DefaultAzureCredential(), allow_preview=True)

    fields = extract_receipt_fields(client.content_understanding, receipt_path)
    add_receipt_to_knowledge_base(client.knowledge_bases, knowledge_base_id, fields)
    print(f"Added receipt {fields.get('order_id')} to the knowledge base.")


if __name__ == "__main__":
    main()
