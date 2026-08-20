"""Cascadia's loyalty-points MCP server: two tools, lookup and redeem,
built on the Model Context Protocol SDK.

Run it locally with `mcp dev solution/mcp_server.py` to test it in the
MCP Inspector (see README.md), or register it in the Foundry Toolbox to
make both tools available to every agent in the project — Lab 09's
classic agent had to define and dispatch its own tools; an agent using
this MCP server doesn't.
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from loyalty_api.loyalty import CustomerNotFoundError, InsufficientPointsError, LoyaltyLedger


def build_server(ledger: LoyaltyLedger) -> FastMCP:
    """Registers both tools against a specific ledger instance.

    A separate function from the module-level `app` below, so tests can
    build a server against a throwaway ledger instead of the shared one
    a real MCP client would talk to.
    """
    server = FastMCP("cascadia-loyalty")

    @server.tool()
    def get_loyalty_points(customer_email: str) -> dict:
        """Look up a customer's current loyalty point balance."""
        try:
            balance = ledger.get_balance(customer_email)
        except CustomerNotFoundError:
            return {"error": f"No loyalty account for {customer_email}"}
        return {"customer_email": customer_email, "balance": balance}

    @server.tool()
    def redeem_loyalty_points(customer_email: str, points: int) -> dict:
        """Redeem loyalty points for a customer, returning the new balance."""
        try:
            return ledger.redeem_points(customer_email, points)
        except CustomerNotFoundError:
            return {"error": f"No loyalty account for {customer_email}"}
        except InsufficientPointsError as exc:
            return {"error": str(exc)}

    return server


app = build_server(LoyaltyLedger())

if __name__ == "__main__":  # pragma: no cover - real stdio server, exercised manually
    app.run()
