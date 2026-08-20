"""A minimal fake for an Azure Cosmos DB container client, used by Lab
20 to exercise the Agent Memory Toolkit pattern offline.

Real Cosmos DB queries run a SQL-like language; this fake accepts a
plain Python predicate instead of parsing SQL — enough to test the
calling code without reimplementing a query engine.
"""

from __future__ import annotations

from collections.abc import Callable


class FakeCosmosContainer:
    def __init__(self) -> None:
        self._items: dict[str, dict] = {}

    def upsert_item(self, body: dict) -> dict:
        self._items[body["id"]] = dict(body)
        return dict(body)

    def read_item(self, item: str, partition_key: str) -> dict:
        return dict(self._items[item])

    def query_items(self, *, predicate: Callable[[dict], bool] | None = None) -> list[dict]:
        items = list(self._items.values())
        if predicate is None:
            return items
        return [item for item in items if predicate(item)]
