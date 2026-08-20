"""Tests for solution/ai_gateway.py.

main() is excluded from coverage — it makes a real network call through
the live gateway, exercised manually, not under test.
"""

import dataclasses

import pytest

from solution.ai_gateway import (
    GatewayCallError,
    build_gateway_request,
    build_rate_limit_policy_xml,
    call_through_gateway,
    parse_rate_limit_policy,
    validate_network_config,
)


def test_rate_limit_policy_round_trips_through_parsing():
    xml = build_rate_limit_policy_xml(calls_per_period=60, renewal_period_seconds=60, daily_quota=2000)

    parsed = parse_rate_limit_policy(xml)

    assert parsed == {"calls_per_period": 60, "renewal_period_seconds": 60, "daily_quota": 2000}


def test_build_gateway_request_sends_the_subscription_key_not_a_model_key():
    request = build_gateway_request(
        gateway_base_url="https://cascadia-ai-gateway.azure-api.net/",
        subscription_key="sub-key-attendee-07",
        deployment_name="cascadia-low-cost",
        messages=[{"role": "user", "content": "hi"}],
    )

    assert request["url"] == "https://cascadia-ai-gateway.azure-api.net/models/chat/completions"
    assert request["headers"]["Ocp-Apim-Subscription-Key"] == "sub-key-attendee-07"
    assert request["json"]["model"] == "cascadia-low-cost"


@dataclasses.dataclass
class FakeHttpResponse:
    status_code: int
    _body: dict | None = None
    text: str = ""

    def json(self) -> dict:
        return self._body


class FakeHttpPost:
    def __init__(self, response: FakeHttpResponse):
        self.response = response
        self.calls: list[dict] = []

    def __call__(self, url, *, headers, json):
        self.calls.append({"url": url, "headers": headers, "json": json})
        return self.response


def test_call_through_gateway_returns_the_parsed_response():
    http_post = FakeHttpPost(FakeHttpResponse(status_code=200, _body={"choices": [{"message": {"content": "ready"}}]}))

    result = call_through_gateway(
        http_post,
        gateway_base_url="https://cascadia-ai-gateway.azure-api.net",
        subscription_key="sub-key-07",
        deployment_name="cascadia-low-cost",
        messages=[{"role": "user", "content": "hi"}],
    )

    assert result == {"choices": [{"message": {"content": "ready"}}]}


def test_call_through_gateway_raises_a_specific_error_for_401():
    http_post = FakeHttpPost(FakeHttpResponse(status_code=401, text="unauthorized"))

    with pytest.raises(GatewayCallError, match="subscription key"):
        call_through_gateway(
            http_post,
            gateway_base_url="https://cascadia-ai-gateway.azure-api.net",
            subscription_key="revoked-key",
            deployment_name="cascadia-low-cost",
            messages=[{"role": "user", "content": "hi"}],
        )


def test_call_through_gateway_raises_a_specific_error_for_429():
    http_post = FakeHttpPost(FakeHttpResponse(status_code=429, text="rate limited"))

    with pytest.raises(GatewayCallError, match="Rate limit"):
        call_through_gateway(
            http_post,
            gateway_base_url="https://cascadia-ai-gateway.azure-api.net",
            subscription_key="sub-key-07",
            deployment_name="cascadia-low-cost",
            messages=[{"role": "user", "content": "hi"}],
        )


def test_call_through_gateway_raises_a_generic_error_for_other_statuses():
    http_post = FakeHttpPost(FakeHttpResponse(status_code=500, text="server error"))

    with pytest.raises(GatewayCallError, match="500"):
        call_through_gateway(
            http_post,
            gateway_base_url="https://cascadia-ai-gateway.azure-api.net",
            subscription_key="sub-key-07",
            deployment_name="cascadia-low-cost",
            messages=[{"role": "user", "content": "hi"}],
        )


def test_validate_network_config_passes_when_properly_locked_down():
    problems = validate_network_config(public_network_access="Disabled", private_endpoint_configured=True)

    assert problems == []


def test_validate_network_config_flags_public_access_still_enabled():
    problems = validate_network_config(public_network_access="Enabled", private_endpoint_configured=False)

    assert any("public_network_access" in problem for problem in problems)


def test_validate_network_config_flags_a_missing_private_endpoint():
    problems = validate_network_config(public_network_access="Disabled", private_endpoint_configured=False)

    assert any("private endpoint" in problem for problem in problems)
