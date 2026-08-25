# Lab 30 — Private networking and the AI Gateway

You'll set project-scoped token limits, call a model through the shared
AI Gateway with your own subscription key instead of a Foundry model
key, and validate the network settings that make the hub reachable only
through it.

**Verified against:** Azure API Management policy XML, as of writing
this workshop.

## Prerequisites

- Lab 04 complete.
- Your instructor has run `infra/gateway/deploy_gateway.sh` and given
  you a subscription key (`infra/gateway/provision_attendee_key.sh`
  output) — see `docs/curriculum.md`, "Provisioning model."

## Step 1: Set project-scoped token limits

1. Open the Foundry Portal's **Control plane** for your project.
2. Under **Limits**, set a tokens-per-minute cap — you did this on your
   own deployment in Lab 05; this time it's protecting the hub's shared
   router from every attendee at once.

## Step 2: Implement the gateway request builder

Open `starter/ai_gateway.py`. Implement four functions:

1. `build_rate_limit_policy_xml()` — the same policy XML
   `infra/gateway/provision_attendee_key.sh` applies, parameterized.
2. `parse_rate_limit_policy()` — read the XML back into its values.
3. `build_gateway_request()` — a request with the subscription key in
   `Ocp-Apim-Subscription-Key`, never a Foundry model key.
4. `call_through_gateway()` — send it, raising `GatewayCallError` with a
   specific message for `401` (bad key) and `429` (rate limited).

Then implement `validate_network_config()`: flag `public_network_access`
that isn't `"Disabled"`, and flag a missing private endpoint when it is.

Run the tests to check your work:

```bash
LAB_TARGET=starter python3 -m pytest tests/ -v
```

**Expected output:** 9 passed.

## Step 3: Call the real gateway

```bash
export AI_GATEWAY_URL="<your gateway URL from your instructor>"
export AI_GATEWAY_SUBSCRIPTION_KEY="<your subscription key>"
python3 starter/ai_gateway.py
```

**Expected output:** a chat completion response, same shape as Lab 03's,
this time routed through the gateway. Notice you never set a Foundry
model key anywhere in this script — the subscription key is the only
credential your code holds.

## Step 4: Hit your own rate limit on purpose

```bash
for i in $(seq 1 70); do python3 starter/ai_gateway.py; done
```

**Expected output:** a `GatewayCallError: Rate limit or quota exceeded`
partway through — your product's policy caps you at 60 calls/minute,
independent of every other attendee's product.

## Step 5: Confirm the network is locked down

Ask your instructor to show `az cognitiveservices account show` for the
hub, and run `validate_network_config()` against the real values.

**Expected output:** an empty problem list — `public_network_access` is
`Disabled`, with a private endpoint in place, so nothing reaches the hub
except through the gateway you just used.

## Where this fits

Lab 33's capstone puts every prior lab's agent behind this same gateway
at once — this lab proves the mechanism works for one call; the capstone
proves it holds up for the whole fleet.
