"""An in-memory stand-in for Cascadia's loyalty points ledger.

Unlike mock_orders_api.orders (read-only fixture data), redeeming points
mutates a balance. A fresh LoyaltyLedger instance per use — instead of
module-level globals — keeps that mutation from leaking between tests
or between unrelated callers.
"""

from __future__ import annotations


class CustomerNotFoundError(LookupError):
    """Raised when a customer has no loyalty account."""


class InsufficientPointsError(ValueError):
    """Raised when a redemption would take a balance below zero."""


class LoyaltyLedger:
    _SEED_BALANCES: dict[str, int] = {
        "maya@example.com": 1200,
        "priya@example.com": 340,
    }

    def __init__(self) -> None:
        self._balances = dict(self._SEED_BALANCES)

    def get_balance(self, customer_email: str) -> int:
        if customer_email not in self._balances:
            raise CustomerNotFoundError(customer_email)
        return self._balances[customer_email]

    def redeem_points(self, customer_email: str, points: int) -> dict:
        """Redeems points and returns the new balance.

        Raises InsufficientPointsError instead of clamping to zero —
        redemptions are a real dollar-value discount here, so silently
        allowing an over-redemption would give away more than the
        customer earned.
        """
        balance = self.get_balance(customer_email)
        if points > balance:
            raise InsufficientPointsError(f"{customer_email} has {balance} points, cannot redeem {points}")
        self._balances[customer_email] = balance - points
        return {
            "customer_email": customer_email,
            "redeemed": points,
            "new_balance": self._balances[customer_email],
        }
