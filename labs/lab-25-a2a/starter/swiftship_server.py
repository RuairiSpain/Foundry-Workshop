"""SwiftShip: an external partner agent, run as its own process,
reached over the A2A protocol.
"""

from __future__ import annotations

_CARRIER_ETAS_BY_ZONE = {
    "pacific-northwest": "1 business day",
    "west-coast": "2 business days",
    "national": "4 business days",
}


def estimate_shipping_eta(*, origin_zone: str, destination_zone: str) -> str:
    """Estimates a shipping ETA between two zones."""
    # TODO(lab-25): raise ValueError if origin_zone or destination_zone
    # isn't in _CARRIER_ETAS_BY_ZONE. If they're the same zone, return
    # that zone's ETA. Otherwise return the "national" ETA.
    raise NotImplementedError("estimate_shipping_eta is not implemented yet")


def main() -> None:
    """Serves `estimate_shipping_eta` as an A2A agent."""
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


if __name__ == "__main__":
    main()
