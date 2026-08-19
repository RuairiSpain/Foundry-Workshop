#!/usr/bin/env bash
# Creates one attendee's Cosmos DB container and scopes a data-plane
# role assignment to that container alone — not the database, not the
# account. Called by attendees/provision_attendee.sh.
#
# Usage: provision_attendee_container.sh <attendee_id> <principal_id>
set -euo pipefail
cd "$(dirname "$0")/.."
source common.sh
require_config "$(pwd)/config.env"

ATTENDEE_ID="${1:?Usage: provision_attendee_container.sh <attendee_id> <principal_id>}"
PRINCIPAL_ID="${2:?Usage: provision_attendee_container.sh <attendee_id> <principal_id>}"
CONTAINER_NAME="mem-${ATTENDEE_ID}"

log "Creating container $CONTAINER_NAME"
az cosmosdb sql container create \
  --account-name "$COSMOS_ACCOUNT_NAME" \
  --resource-group "$HUB_RESOURCE_GROUP" \
  --database-name "$COSMOS_DATABASE_NAME" \
  --name "$CONTAINER_NAME" \
  --partition-key-path "/threadId" \
  --throughput 400 \
  --output none

COSMOS_ACCOUNT_ID=$(az cosmosdb show \
  --name "$COSMOS_ACCOUNT_NAME" \
  --resource-group "$HUB_RESOURCE_GROUP" \
  --query id -o tsv)

# Cosmos DB's data-plane RBAC is a separate mechanism from Azure RBAC —
# this role definition and assignment live inside the Cosmos account,
# not at the subscription/resource-group level. The relative scope
# string is what confines the grant to this one container.
log "Scoping Data Contributor to $CONTAINER_NAME only"
# 00000000-0000-0000-0000-000000000002 is the built-in Data Contributor
# role ID. Confirm it with:
#   az cosmosdb sql role definition list --account-name "$COSMOS_ACCOUNT_NAME" \
#     --resource-group "$HUB_RESOURCE_GROUP" -o table
az cosmosdb sql role assignment create \
  --account-name "$COSMOS_ACCOUNT_NAME" \
  --resource-group "$HUB_RESOURCE_GROUP" \
  --role-definition-id "00000000-0000-0000-0000-000000000002" \
  --principal-id "$PRINCIPAL_ID" \
  --scope "${COSMOS_ACCOUNT_ID}/dbs/${COSMOS_DATABASE_NAME}/colls/${CONTAINER_NAME}" \
  --output none

log "Container ready: $CONTAINER_NAME, scoped to principal $PRINCIPAL_ID"
