"""Stores conversation turns in a Cosmos DB container and distills them
into a simple customer profile — the Agent Memory Toolkit pattern,
against your own per-attendee container instead of Lab 19's managed
memory store.
"""

from __future__ import annotations

import dataclasses
import re
import uuid

SKU_PATTERN = re.compile(r"\b[A-Z]+-[A-Z0-9]+(?:-[A-Z0-9]+)?\b")


def build_memory_document(*, thread_id: str, role: str, content: str, customer_email: str) -> dict:
    """Builds one Cosmos document for a conversation turn."""
    # TODO(lab-20): return a dict with "id" (str(uuid.uuid4())),
    # "threadId" (thread_id — the partition key), "customerEmail",
    # "role", and "content".
    raise NotImplementedError("build_memory_document is not implemented yet")


def store_turn(container, *, thread_id: str, role: str, content: str, customer_email: str) -> dict:
    """Writes one conversation turn to the container."""
    # TODO(lab-20): build a document with build_memory_document() and
    # call container.upsert_item() with it.
    raise NotImplementedError("store_turn is not implemented yet")


def search_memory_by_customer(container, *, customer_email: str) -> list[dict]:
    """Returns every stored turn for one customer, across all threads."""
    # TODO(lab-20): call container.query_items() with
    # query="SELECT * FROM c WHERE c.customerEmail = @email",
    # parameters=[{"name": "@email", "value": customer_email}], and
    # enable_cross_partition_query=True — customerEmail isn't the
    # partition key, so this needs to search across all of them. Wrap
    # the result in list(...).
    raise NotImplementedError("search_memory_by_customer is not implemented yet")


@dataclasses.dataclass
class CustomerProfile:
    customer_email: str
    mentioned_skus: list[str]
    turn_count: int


def distill_profile(turns: list[dict]) -> CustomerProfile:
    """Derives a small profile from raw turns: every SKU mentioned, and
    how many turns exist.
    """
    # TODO(lab-20): raise ValueError for an empty list — the message must
    # mention "zero turns". Otherwise collect every SKU_PATTERN match
    # across all turns' content into a set, and return a CustomerProfile
    # with the first turn's customerEmail, a sorted list of SKUs, and the
    # turn count.
    raise NotImplementedError("distill_profile is not implemented yet")


def main() -> None:
    import os

    from azure.cosmos import CosmosClient

    cosmos_client = CosmosClient(
        url=os.environ["COSMOS_ACCOUNT_ENDPOINT"], credential=os.environ["COSMOS_ACCOUNT_KEY"]
    )
    database = cosmos_client.get_database_client(os.environ.get("COSMOS_DATABASE_NAME", "workshop-memory"))
    container = database.get_container_client(os.environ["COSMOS_CONTAINER_NAME"])

    store_turn(
        container,
        thread_id="thread-001",
        role="user",
        content="I'm eyeing the TENT-2P-GRN for a trip next month.",
        customer_email="maya@example.com",
    )
    turns = search_memory_by_customer(container, customer_email="maya@example.com")
    profile = distill_profile(turns)
    print(profile)


if __name__ == "__main__":
    main()
