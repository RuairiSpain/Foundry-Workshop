#!/usr/bin/env bash
# Creates the instructor's Foundry hub and deploys the shared router
# model. Run once per workshop delivery, before attendees arrive.
set -euo pipefail
cd "$(dirname "$0")/.."
source common.sh
require_config "$(pwd)/config.env"

log "Creating resource group $HUB_RESOURCE_GROUP"
if ! resource_group_exists "$HUB_RESOURCE_GROUP"; then
  az group create \
    --name "$HUB_RESOURCE_GROUP" \
    --location "$LOCATION" \
    --output none
else
  log "Resource group already exists, skipping"
fi

log "Creating Foundry hub resource $HUB_ACCOUNT_NAME"
# --allow-project-management is what turns this into a hub: without it,
# attendees can't create projects under this account.
az cognitiveservices account create \
  --name "$HUB_ACCOUNT_NAME" \
  --resource-group "$HUB_RESOURCE_GROUP" \
  --kind AIServices \
  --sku S0 \
  --location "$LOCATION" \
  --custom-domain "$HUB_ACCOUNT_NAME" \
  --allow-project-management \
  --output none

log "Deploying shared router model $ROUTER_MODEL_NAME"
# This deployment is intentionally hub-level, not project-level — every
# attendee's project connects to it instead of deploying their own
# router. See docs/curriculum.md, "Provisioning model".
az cognitiveservices account deployment create \
  --name "$HUB_ACCOUNT_NAME" \
  --resource-group "$HUB_RESOURCE_GROUP" \
  --deployment-name "$ROUTER_DEPLOYMENT_NAME" \
  --model-name "$ROUTER_MODEL_NAME" \
  --model-version "$ROUTER_MODEL_VERSION" \
  --model-format "$ROUTER_MODEL_FORMAT" \
  --sku-capacity 10 \
  --sku-name Standard \
  --output none

log "Hub ready: $HUB_ACCOUNT_NAME in $HUB_RESOURCE_GROUP"
log "Next: attendees/provision_all.sh grants each attendee Azure AI Developer on this resource group."
