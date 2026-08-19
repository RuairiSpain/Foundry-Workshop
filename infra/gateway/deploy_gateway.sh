#!/usr/bin/env bash
# Creates the one shared AI Gateway in front of the hub. Every attendee
# gets a key into this instance — see gateway/provision_attendee_key.sh.
# We do not give attendees their own gateway; see docs/curriculum.md,
# "Provisioning model".
#
# Consumption SKU deploys faster and bills per call instead of per
# instance-hour, which fits a workshop's short-lived, bursty traffic
# better than Developer or Standard. Even so, budget real time for this
# step and start it before anything else.
set -euo pipefail
cd "$(dirname "$0")/.."
source common.sh
require_config "$(pwd)/config.env"

log "Creating API Management instance $APIM_NAME ($APIM_SKU tier)"
log "This can take a while. It runs in the foreground; open a second terminal for the rest of infra/ if you don't want to wait."
az apim create \
  --name "$APIM_NAME" \
  --resource-group "$HUB_RESOURCE_GROUP" \
  --publisher-email "$APIM_PUBLISHER_EMAIL" \
  --publisher-name "$APIM_PUBLISHER_NAME" \
  --sku-name "$APIM_SKU" \
  --output none

HUB_ENDPOINT="https://${HUB_ACCOUNT_NAME}.openai.azure.com"

log "Importing the hub's model endpoint as an API"
az apim api create \
  --resource-group "$HUB_RESOURCE_GROUP" \
  --service-name "$APIM_NAME" \
  --api-id foundry-models \
  --path "models" \
  --display-name "Cascadia Foundry Models" \
  --service-url "$HUB_ENDPOINT" \
  --protocols https \
  --subscription-required true \
  --output none

log "Granting the gateway managed-identity access to the hub"
# The gateway authenticates to the hub as itself. Attendees hold a
# gateway subscription key, never a hub model key.
az apim update \
  --resource-group "$HUB_RESOURCE_GROUP" \
  --name "$APIM_NAME" \
  --set identity.type=SystemAssigned \
  --output none

APIM_PRINCIPAL_ID=$(az apim show \
  --resource-group "$HUB_RESOURCE_GROUP" \
  --name "$APIM_NAME" \
  --query identity.principalId -o tsv)

HUB_RESOURCE_ID=$(az cognitiveservices account show \
  --name "$HUB_ACCOUNT_NAME" \
  --resource-group "$HUB_RESOURCE_GROUP" \
  --query id -o tsv)

az role assignment create \
  --assignee "$APIM_PRINCIPAL_ID" \
  --role "Cognitive Services OpenAI User" \
  --scope "$HUB_RESOURCE_ID" \
  --output none

log "Gateway ready: $APIM_NAME"
log "Next: attendees/provision_all.sh creates one product and key per attendee."
