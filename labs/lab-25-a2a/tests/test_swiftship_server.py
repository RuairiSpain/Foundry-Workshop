"""Tests for solution/swiftship_server.py.

main() is excluded from coverage — it wires a real A2A server process,
exercised manually, not under test.
"""

import pytest

from solution.swiftship_server import estimate_shipping_eta


def test_same_zone_returns_that_zones_eta():
    assert estimate_shipping_eta(origin_zone="pacific-northwest", destination_zone="pacific-northwest") == (
        "1 business day"
    )


def test_cross_zone_returns_the_national_eta():
    assert estimate_shipping_eta(origin_zone="pacific-northwest", destination_zone="west-coast") == (
        "4 business days"
    )


def test_unknown_origin_zone_raises():
    with pytest.raises(ValueError, match="mars"):
        estimate_shipping_eta(origin_zone="mars", destination_zone="national")


def test_unknown_destination_zone_raises():
    with pytest.raises(ValueError, match="mars"):
        estimate_shipping_eta(origin_zone="national", destination_zone="mars")
