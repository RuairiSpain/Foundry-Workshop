"""Tests for solution/durable_fulfillment.py.

register_functions() and the module-level `app` are excluded from
coverage — decorator wiring for the real Functions host, exercised
manually, not under test.

The orchestrator is a plain generator function, so its branching logic
is testable by driving it directly with `next()` and `.send()` — the
standard way to unit-test a Durable Functions orchestrator without a
running host. `FakeDurableContext` stands in for the real
`DurableOrchestrationContext`; it only needs `get_input()` and
`call_activity()`, since that's all the orchestrator calls.
"""

import pytest

from solution.durable_fulfillment import (
    check_stock_activity,
    confirm_order_activity,
    order_fulfillment_orchestrator,
    reserve_item_activity,
)


class FakeDurableContext:
    def __init__(self, input_value):
        self._input = input_value

    def get_input(self):
        return self._input

    def call_activity(self, name, input_=None):
        return {"activity": name, "input": input_}


def test_check_stock_activity_sums_stock_across_branches():
    result = check_stock_activity("CO-10231")

    assert result == {"sku": "TENT-2P-GRN", "total_stock": 26}


def test_reserve_item_activity_confirms_the_reservation():
    result = reserve_item_activity({"sku": "TENT-2P-GRN"})

    assert result == {"sku": "TENT-2P-GRN", "reserved": True}


def test_confirm_order_activity_returns_the_final_confirmation():
    result = confirm_order_activity("CO-10231")

    assert result["order_id"] == "CO-10231"
    assert result["status"] == "confirmed"
    assert result["items"][0]["sku"] == "TENT-2P-GRN"


def test_orchestrator_happy_path_runs_all_three_activities_in_order():
    context = FakeDurableContext("CO-10231")
    gen = order_fulfillment_orchestrator(context)

    first_call = next(gen)
    assert first_call == {"activity": "CheckStock", "input": "CO-10231"}

    second_call = gen.send({"sku": "TENT-2P-GRN", "total_stock": 26})
    assert second_call == {"activity": "ReserveItem", "input": {"sku": "TENT-2P-GRN"}}

    third_call = gen.send({"sku": "TENT-2P-GRN", "reserved": True})
    assert third_call == {"activity": "ConfirmOrder", "input": "CO-10231"}

    with pytest.raises(StopIteration) as exc_info:
        gen.send({"order_id": "CO-10231", "status": "confirmed", "items": []})

    assert exc_info.value.value == {"order_id": "CO-10231", "status": "confirmed", "items": []}


def test_orchestrator_stops_early_when_out_of_stock():
    context = FakeDurableContext("CO-99999")
    gen = order_fulfillment_orchestrator(context)

    first_call = next(gen)
    assert first_call == {"activity": "CheckStock", "input": "CO-99999"}

    with pytest.raises(StopIteration) as exc_info:
        gen.send({"sku": "SOME-SKU", "total_stock": 0})

    assert exc_info.value.value == {"status": "out_of_stock", "order_id": "CO-99999"}


def test_orchestrator_replay_is_deterministic_given_the_same_inputs():
    """Simulates a restart: build a fresh generator and replay it with
    the exact same activity results already recorded. It must reach the
    same point with the same pending call — which is what lets the real
    runtime resume instead of starting the whole order over.
    """
    context = FakeDurableContext("CO-10231")

    first_run = order_fulfillment_orchestrator(context)
    next(first_run)
    replayed_call = first_run.send({"sku": "TENT-2P-GRN", "total_stock": 26})

    second_run = order_fulfillment_orchestrator(context)
    next(second_run)
    resumed_call = second_run.send({"sku": "TENT-2P-GRN", "total_stock": 26})

    assert replayed_call == resumed_call
