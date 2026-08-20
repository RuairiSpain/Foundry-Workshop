"""SwiftShip: an external partner agent, run as its own process,
reached over the A2A protocol. This is a stand-in we run ourselves —
good enough to prove the A2A pattern end to end, not a live third-party
integration.
"""

from __future__ import annotations

_CARRIER_ETAS_BY_ZONE = {
    "pacific-northwest": "1 business day",
    "west-coast": "2 business days",
    "national": "4 business days",
}


def estimate_shipping_eta(*, origin_zone: str, destination_zone: str) -> str:
    """Estimates a shipping ETA between two zones.

    Raises ValueError for an unknown zone instead of guessing —
    SwiftShip's real system would reject an unroutable request the same
    way, and a silent guess here would be worse than an error.
    """
    if origin_zone not in _CARRIER_ETAS_BY_ZONE or destination_zone not in _CARRIER_ETAS_BY_ZONE:
        raise ValueError(f"Unknown shipping zone: {origin_zone!r} or {destination_zone!r}")
    if origin_zone == destination_zone:
        return _CARRIER_ETAS_BY_ZONE[origin_zone]
    return _CARRIER_ETAS_BY_ZONE["national"]


def main() -> None:  # pragma: no cover - real A2A server process, exercised manually
    """Serves `estimate_shipping_eta` as an A2A agent.

    This is the code that would run as SwiftShip's own process — a
    separate `python3 swiftship_server.py` next to the Trip Planner's
    process, not something the Trip Planner imports directly. A2AExecutor
    wraps a local Agent, so the function above is wrapped in one here.
    """
    from agent_framework import Agent
    from agent_framework.a2a import A2AExecutor

    def shipping_eta_tool(origin_zone: str, destination_zone: str) -> str:
        """Estimate a shipping ETA between two zones."""
        return estimate_shipping_eta(origin_zone=origin_zone, destination_zone=destination_zone)

    swiftship_agent = Agent(
        client=None,  # SwiftShip would configure its own model client here.
        name="swiftship",
        instructions="Answer shipping ETA questions using shipping_eta_tool.",
        tools=[shipping_eta_tool],
    )
    executor = A2AExecutor(agent=swiftship_agent)
    print(f"SwiftShip A2A executor ready: {executor}")
    # A real deployment binds this executor to an ASGI server (uvicorn,
    # hypercorn) exposing the A2A JSON-RPC endpoint. See README.md.


if __name__ == "__main__":  # pragma: no cover
    main()
