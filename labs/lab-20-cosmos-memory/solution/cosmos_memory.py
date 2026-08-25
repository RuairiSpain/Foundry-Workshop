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
    """Builds one Cosmos document for a conversation turn.

    `threadId` is the partition key: every turn from one thread lands in
    the same partition, which is what makes reading back a thread's full
    history a single-partition query instead of a fan-out.
    """
    return {
        "id": str(uuid.uuid4()),
        "threadId": thread_id,
        "customerEmail": customer_email,
        "role": role,
        "content": content,
    }


def store_turn(container, *, thread_id: str, role: str, content: str, customer_email: str) -> dict:
    """Writes one conversation turn to the container."""
    document = build_memory_document(thread_id=thread_id, role=role, content=content, customer_email=customer_email)
    return container.upsert_item(document)


def search_memory_by_customer(container, *, customer_email: str) -> list[dict]:
    """Returns every stored turn for one customer, across all threads.

    Cross-partition, since `threadId` (not `customerEmail`) is the
    partition key — one customer's turns can be spread across many
    threads/partitions, so `enable_cross_partition_query=True` is
    required for this query to see all of them.
    """
    return list(
        container.query_items(
            query="SELECT * FROM c WHERE c.customerEmail = @email",
            parameters=[{"name": "@email", "value": customer_email}],
            enable_cross_partition_query=True,
        )
    )


@dataclasses.dataclass
class CustomerProfile:
    customer_email: str
    mentioned_skus: list[str]
    turn_count: int


def distill_profile(turns: list[dict]) -> CustomerProfile:
    """Derives a small profile from raw turns: every SKU mentioned, and
    how many turns exist — a simplified stand-in for the Agent Memory
    Toolkit's thread summaries and extracted facts.

    Raises ValueError for an empty list instead of returning an empty
    profile, since "no turns" and "a customer with zero SKUs mentioned"
    are different situations a caller needs to tell apart.
    """
    if not turns:
        raise ValueError("Cannot distill a profile from zero turns")
    customer_email = turns[0]["customerEmail"]
    skus: set[str] = set()
    for turn in turns:
        skus.update(SKU_PATTERN.findall(turn["content"]))
    return CustomerProfile(customer_email=customer_email, mentioned_skus=sorted(skus), turn_count=len(turns))


def main() -> None:  # pragma: no cover - real Cosmos SDK wiring and CLI entry point, exercised manually
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


if __name__ == "__main__":  # pragma: no cover
    main()
