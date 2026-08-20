"""Builds the same per-attendee rate-limit policy
`infra/gateway/provision_attendee_key.sh` applies, calls a model through
the shared AI Gateway with an attendee's subscription key instead of a
Foundry model key, and validates a project's private-networking config.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET


def build_rate_limit_policy_xml(*, calls_per_period: int, renewal_period_seconds: int, daily_quota: int) -> str:
    """Builds the APIM policy XML capping one attendee's product.

    Scoped with `@(context.Subscription.Id)` as the counter key, so the
    limit applies per subscription key — per attendee — not to the
    gateway as a whole.
    """
    return f"""<policies>
  <inbound>
    <base />
    <rate-limit-by-key calls="{calls_per_period}" renewal-period="{renewal_period_seconds}"
      counter-key="@(context.Subscription.Id)" />
    <quota-by-key calls="{daily_quota}" renewal-period="86400"
      counter-key="@(context.Subscription.Id)" />
  </inbound>
  <backend><base /></backend>
  <outbound><base /></outbound>
  <on-error><base /></on-error>
</policies>"""


def parse_rate_limit_policy(policy_xml: str) -> dict:
    """Reads a policy XML back into its calls/renewal/quota values.

    Used to verify a policy already applied to a product in the Portal
    matches what this lab expects, without re-deriving it by eye.
    """
    root = ET.fromstring(policy_xml)
    rate_limit = root.find("./inbound/rate-limit-by-key")
    quota = root.find("./inbound/quota-by-key")
    return {
        "calls_per_period": int(rate_limit.attrib["calls"]),
        "renewal_period_seconds": int(rate_limit.attrib["renewal-period"]),
        "daily_quota": int(quota.attrib["calls"]),
    }


def build_gateway_request(*, gateway_base_url: str, subscription_key: str, deployment_name: str, messages: list[dict]) -> dict:
    """Builds the HTTP request an app sends through the gateway.

    The subscription key goes in `Ocp-Apim-Subscription-Key` — an app
    behind the gateway never holds a Foundry model key at all, only this
    rotatable, per-attendee key.
    """
    return {
        "url": f"{gateway_base_url.rstrip('/')}/models/chat/completions",
        "headers": {"Ocp-Apim-Subscription-Key": subscription_key, "Content-Type": "application/json"},
        "json": {"model": deployment_name, "messages": messages},
    }


class GatewayCallError(RuntimeError):
    """Raised when a call through the gateway fails, with the HTTP status attached."""


def call_through_gateway(
    http_post, *, gateway_base_url: str, subscription_key: str, deployment_name: str, messages: list[dict]
) -> dict:
    """Sends a chat completion request through the gateway and returns the parsed JSON.

    `http_post` is injected so tests can substitute a fake instead of a
    real network call — the same boundary Lab 10's function tool client
    crossed for its own HTTP dependency.
    """
    request = build_gateway_request(
        gateway_base_url=gateway_base_url, subscription_key=subscription_key, deployment_name=deployment_name, messages=messages
    )
    response = http_post(request["url"], headers=request["headers"], json=request["json"])
    if response.status_code == 401:
        raise GatewayCallError("Gateway rejected the subscription key — confirm it hasn't been rotated or revoked.")
    if response.status_code == 429:
        raise GatewayCallError("Rate limit or quota exceeded for this attendee's product.")
    if response.status_code != 200:
        raise GatewayCallError(f"Gateway call failed with {response.status_code}: {response.text}")
    return response.json()


def validate_network_config(*, public_network_access: str, private_endpoint_configured: bool) -> list[str]:
    """Checks a project's network settings against Lab 30's requirement:
    public access disabled, with a private endpoint taking its place.

    Returns a list of problems instead of raising, so a caller can
    report every misconfiguration at once instead of fixing one,
    re-running, and finding the next.
    """
    problems = []
    if public_network_access != "Disabled":
        problems.append(f"public_network_access is {public_network_access!r}, expected 'Disabled'.")
    if public_network_access == "Disabled" and not private_endpoint_configured:
        problems.append("Public access is disabled but no private endpoint is configured — the project is unreachable.")
    return problems


def main() -> None:  # pragma: no cover - real network call and CLI entry point, exercised manually
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


if __name__ == "__main__":  # pragma: no cover
    main()
