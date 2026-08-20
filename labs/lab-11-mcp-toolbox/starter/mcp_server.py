"""Cascadia's loyalty-points MCP server: two tools, lookup and redeem,
built on the Model Context Protocol SDK.
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from loyalty_api.loyalty import CustomerNotFoundError, InsufficientPointsError, LoyaltyLedger


def build_server(ledger: LoyaltyLedger) -> FastMCP:
    """Registers both tools against a specific ledger instance."""
    server = FastMCP("cascadia-loyalty")

    @server.tool()
    def get_loyalty_points(customer_email: str) -> dict:
        """Look up a customer's current loyalty point balance."""
        # TODO(lab-11): call ledger.get_balance(customer_email). Catch
        # CustomerNotFoundError and return {"error": ...} instead of
        # raising. Otherwise return {"customer_email": ..., "balance": ...}.
        raise NotImplementedError("get_loyalty_points is not implemented yet")

    @server.tool()
    def redeem_loyalty_points(customer_email: str, points: int) -> dict:
        """Redeem loyalty points for a customer, returning the new balance."""
        # TODO(lab-11): call ledger.redeem_points(customer_email, points).
        # Catch CustomerNotFoundError and InsufficientPointsError and
        # return {"error": ...} for each instead of raising.
        raise NotImplementedError("redeem_loyalty_points is not implemented yet")

    return server


app = build_server(LoyaltyLedger())

if __name__ == "__main__":
    app.run()
