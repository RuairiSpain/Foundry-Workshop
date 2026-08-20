"""Extracts structured fields from a receipt with Content Understanding,
validates the extraction, and feeds it into Lab 07's knowledge base as a
new source.
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
    return content_understanding_client.analyze(file_path=str(file_path), schema=schema)


@dataclasses.dataclass
class ValidationResult:
    missing_fields: list[str]

    @property
    def is_complete(self) -> bool:
        return not self.missing_fields


def validate_extraction(fields: dict, *, required_fields: list[str] = REQUIRED_FIELDS) -> ValidationResult:
    """Checks that every required field came back with a non-empty value.

    Content Understanding can return a schema with a field present but
    empty — low confidence, illegible text — which a simple
    `"order_id" in fields` check would miss.
    """
    missing = [field for field in required_fields if not fields.get(field)]
    return ValidationResult(missing_fields=missing)


def build_knowledge_base_source(extracted_fields: dict) -> dict:
    """Shapes an extraction result as a structured knowledge base source —
    the same source type Lab 07 used for the product catalog.
    """
    return {"type": "structured", "data": extracted_fields}


def add_receipt_to_knowledge_base(knowledge_bases_client, knowledge_base_id: str, extracted_fields: dict) -> dict:
    """Adds one validated extraction to an existing knowledge base.

    Raises ValueError instead of silently skipping validation — a
    receipt missing its order_id or customer_email is useless as a
    grounding source no matter how it's added.
    """
    validation = validate_extraction(extracted_fields)
    if not validation.is_complete:
        raise ValueError(f"Extraction is missing required fields: {validation.missing_fields}")
    source = build_knowledge_base_source(extracted_fields)
    return knowledge_bases_client.add_source(knowledge_base_id, source)


def main() -> None:  # pragma: no cover - real SDK wiring and CLI entry point, exercised manually
    import os

    from azure.ai.projects import AIProjectClient
    from azure.identity import DefaultAzureCredential

    receipt_path = Path(__file__).resolve().parents[3] / "case-study" / "receipts-and-specs" / "receipt-CO-10231.txt"
    endpoint = os.environ["FOUNDRY_PROJECT_ENDPOINT"]
    knowledge_base_id = os.environ["FOUNDRY_IQ_KNOWLEDGE_BASE_ID"]
    client = AIProjectClient(endpoint=endpoint, credential=DefaultAzureCredential())

    fields = extract_receipt_fields(client.content_understanding, receipt_path)
    add_receipt_to_knowledge_base(client.knowledge_bases, knowledge_base_id, fields)
    print(f"Added receipt {fields.get('order_id')} to the knowledge base.")


if __name__ == "__main__":  # pragma: no cover
    main()
