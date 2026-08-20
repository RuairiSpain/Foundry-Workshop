"""Builds the same per-attendee rate-limit policy
`infra/gateway/provision_attendee_key.sh` applies, calls a model through
the shared AI Gateway with an attendee's subscription key instead of a
Foundry model key, and validates a project's private-networking config.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET


def build_rate_limit_policy_xml(*, calls_per_period: int, renewal_period_seconds: int, daily_quota: int) -> str:
    """Builds the APIM policy XML capping one attendee's product."""
    # TODO(lab-30): return the policy XML with <rate-limit-by-key> using
    # calls_per_period and renewal_period_seconds, and <quota-by-key>
    # using daily_quota with a 86400-second renewal period. Both keyed
    # on "@(context.Subscription.Id)".
    raise NotImplementedError("build_rate_limit_policy_xml is not implemented yet")


def parse_rate_limit_policy(policy_xml: str) -> dict:
    """Reads a policy XML back into its calls/renewal/quota values."""
    # TODO(lab-30): parse policy_xml with ET.fromstring(), find the
    # rate-limit-by-key and quota-by-key elements under ./inbound/, and
    # return a dict with calls_per_period, renewal_period_seconds, and
    # daily_quota as ints.
    raise NotImplementedError("parse_rate_limit_policy is not implemented yet")


def build_gateway_request(*, gateway_base_url: str, subscription_key: str, deployment_name: str, messages: list[dict]) -> dict:
    """Builds the HTTP request an app sends through the gateway."""
    # TODO(lab-30): return a dict with "url" (gateway_base_url stripped
    # of a trailing slash, plus "/models/chat/completions"), "headers"
    # (with "Ocp-Apim-Subscription-Key" set to subscription_key), and
    # "json" (with "model" and "messages").
    raise NotImplementedError("build_gateway_request is not implemented yet")


class GatewayCallError(RuntimeError):
    """Raised when a call through the gateway fails, with the HTTP status attached."""


def call_through_gateway(
    http_post, *, gateway_base_url: str, subscription_key: str, deployment_name: str, messages: list[dict]
) -> dict:
    """Sends a chat completion request through the gateway and returns the parsed JSON."""
    # TODO(lab-30): build the request with build_gateway_request(), call
    # http_post(url, headers=..., json=...), and raise GatewayCallError
    # with a specific message for 401, 429, and any other non-200
    # status. Otherwise return response.json().
    raise NotImplementedError("call_through_gateway is not implemented yet")


def validate_network_config(*, public_network_access: str, private_endpoint_configured: bool) -> list[str]:
    """Checks a project's network settings against Lab 30's requirement."""
    # TODO(lab-30): return a list of problem strings: one if
    # public_network_access isn't "Disabled", and one if it is Disabled
    # but private_endpoint_configured is False.
    raise NotImplementedError("validate_network_config is not implemented yet")


def main() -> None:
    import os

    import requests

    result = call_through_gateway(
        requests.post,
        gateway_base_url=os.environ["AI_GATEWAY_URL"],
        subscription_key=os.environ["AI_GATEWAY_SUBSCRIPTION_KEY"],
        deployment_name=os.environ.get("LOW_COST_DEPLOYMENT", "cascadia-low-cost"),
        messages=[{"role": "user", "content": "Reply with the single word: ready."}],
    )
    print(result)


if __name__ == "__main__":
    main()
