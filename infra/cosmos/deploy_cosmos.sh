#!/usr/bin/env bash
# Creates the shared Cosmos DB account and database for Lab 20. Per-
# attendee containers are created later by attendees/provision_all.sh,
# since they need the roster.
set -euo pipefail
cd "$(dirname "$0")/.."
source common.sh
require_config "$(pwd)/config.env"

log "Creating Cosmos DB account $COSMOS_ACCOUNT_NAME (serverless)"
# EnableServerless bills per request instead of per hour of provisioned
# throughput — the same reasoning that put the AI Gateway on APIM's
# Consumption tier (see gateway/deploy_gateway.sh). A workshop's memory
# traffic is bursty and small, so a multi-day delivery costs close to
# nothing overnight instead of paying for idle RU/s. This is why
# cosmos/provision_attendee_container.sh doesn't pass --throughput:
# serverless accounts reject an explicit throughput on their containers.
az cosmosdb create \
  --name "$COSMOS_ACCOUNT_NAME" \
  --resource-group "$HUB_RESOURCE_GROUP" \
  --locations regionName="$LOCATION" failoverPriority=0 \
  --capabilities EnableServerless \
  --default-consistency-level Session \
  --output none

log "Creating database $COSMOS_DATABASE_NAME"
az cosmosdb sql database create \
  --account-name "$COSMOS_ACCOUNT_NAME" \
  --resource-group "$HUB_RESOURCE_GROUP" \
  --name "$COSMOS_DATABASE_NAME" \
  --output none

log "Cosmos DB ready: $COSMOS_ACCOUNT_NAME / $COSMOS_DATABASE_NAME"
log "Next: attendees/provision_all.sh creates one container per attendee."
