# Workshop infrastructure

Scripts that stand up the hub-and-spoke architecture from
`docs/curriculum.md`. Run them in this order, once per workshop delivery.

1. `hub/deploy_hub.sh` — instructor's Foundry hub and the shared router
   model.
2. `cosmos/deploy_cosmos.sh` — shared Cosmos DB account and database.
3. `gateway/deploy_gateway.sh` — shared AI Gateway in front of the hub.
   Takes 30–45 minutes. Start it before anything else, in the
   background, and come back to it.
4. `attendees/provision_all.sh` — loops over your roster and, per
   attendee, creates a Foundry project under the hub, a Cosmos DB
   container, and a gateway subscription key.

Run `teardown.sh` after the workshop. Nothing here needs tearing down
between sessions purely to save money — the AI Gateway is APIM
Consumption tier and the Cosmos DB account is serverless, so both bill
per call instead of per idle hour, the same way every model deployment
already bills per token. `teardown.sh` is still how you eventually stop
paying for storage and reclaim the resource names once the workshop is
fully over.

## Configuration

Copy `config.env.example` to `config.env` and fill in your subscription,
resource group, and location. Every script sources it.

```bash
cp infra/config.env.example infra/config.env
```

## Roster

`attendees/roster.example.csv` shows the expected format: one row per
attendee, `attendee_id,principal_id`. `attendee_id` becomes the suffix on
every per-attendee resource (`mem-<attendee_id>`, project name, gateway
product name). `principal_id` is the attendee's Azure AD object ID —
get it with `az ad user show --id <email> --query id -o tsv` before you
run `provision_all.sh`.

## What's per-attendee vs. shared

See "Provisioning model" in `docs/curriculum.md` for the reasoning.
Shared: the hub resource, the router model deployment, the Cosmos DB
account, the AI Gateway instance. Per-attendee: the Foundry project, the
low-cost model deployment inside it, the Cosmos DB container, the
gateway subscription key.
