"""A minimal fake for an Azure Cosmos DB container client, used by Lab
20 to exercise the Agent Memory Toolkit pattern offline.

Verified against the real `azure-cosmos` 4.16.3 `ContainerProxy`:
`query_items()` takes a `query` SQL string and a `parameters` list of
`{"name": ..., "value": ...}` dicts, never a Python callable — a
`predicate=` kwarg isn't part of the real API, so passing one there
gets silently absorbed into the real client's `**kwargs` and ignored,
which makes an unfiltered, full-container scan look like a working
filter. This fake takes the same `query`/`parameters` shape the real
service does, and understands one clause shape: `WHERE c.<field> =
@param`, matched against the single bound parameter — enough to test
the calling code without reimplementing a query engine.
"""

from __future__ import annotations

import re

_WHERE_EQUALS = re.compile(r"WHERE\s+c\.(\w+)\s*=\s*(@\w+)", re.IGNORECASE)


class FakeCosmosContainer:
    def __init__(self) -> None:
        self._items: dict[str, dict] = {}

    def upsert_item(self, body: dict) -> dict:
        self._items[body["id"]] = dict(body)
        return dict(body)

    def read_item(self, item: str, partition_key: str) -> dict:
        return dict(self._items[item])

    def query_items(self, *, query: str | None = None, parameters: list[dict] | None = None, **kwargs) -> list[dict]:
        items = list(self._items.values())
        if query is None:
            return items
        match = _WHERE_EQUALS.search(query)
        if not match or not parameters:
            return items
        field, placeholder = match.group(1), match.group(2)
        value = next((p["value"] for p in parameters if p["name"] == placeholder), None)
        return [item for item in items if item.get(field) == value]
