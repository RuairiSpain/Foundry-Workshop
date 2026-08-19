#!/usr/bin/env bash
# Provisions everything one attendee needs: a Foundry project under the
# hub, RBAC on the hub resource group, a Cosmos DB container, and a
# gateway subscription key. Called by provision_all.sh; safe to run
# standalone for a single late-arriving attendee.
#
# Usage: provision_attendee.sh <attendee_id> <principal_id>
set -euo pipefail
cd "$(dirname "$0")/.."
source common.sh
require_config "$(pwd)/config.env"

ATTENDEE_ID="${1:?Usage: provision_attendee.sh <attendee_id> <principal_id>}"
PRINCIPAL_ID="${2:?Usage: provision_attendee.sh <attendee_id> <principal_id>}"

log "=== Provisioning $ATTENDEE_ID ==="

HUB_RESOURCE_ID=$(az cognitiveservices account show \
  --name "$HUB_ACCOUNT_NAME" \
  --resource-group "$HUB_RESOURCE_GROUP" \
  --query id -o tsv)

log "Granting Azure AI Developer on the hub resource group"
# Scoped to the resource group, not the subscription: this is enough to
# create a project and use the hub's shared models, and nothing more.
az role assignment create \
  --assignee "$PRINCIPAL_ID" \
  --role "Azure AI Developer" \
  --scope "$HUB_RESOURCE_ID" \
  --output none

log "Creating Foundry project for $ATTENDEE_ID"
az cognitiveservices account project create \
  --account-name "$HUB_ACCOUNT_NAME" \
  --resource-group "$HUB_RESOURCE_GROUP" \
  --name "proj-${ATTENDEE_ID}" \
  --output none

log "Creating Cosmos DB container for $ATTENDEE_ID"
./cosmos/provision_attendee_container.sh "$ATTENDEE_ID" "$PRINCIPAL_ID"

log "Creating gateway key for $ATTENDEE_ID"
GATEWAY_KEY=$(./gateway/provision_attendee_key.sh "$ATTENDEE_ID" | tail -n1)

log "=== $ATTENDEE_ID ready ==="
echo "${ATTENDEE_ID},proj-${ATTENDEE_ID},${GATEWAY_KEY}"
