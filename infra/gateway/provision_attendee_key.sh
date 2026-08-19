#!/usr/bin/env bash
# Creates one attendee's product, rate-limit policy, and subscription
# key inside the shared gateway. Called by
# attendees/provision_attendee.sh — attendees never deploy their own
# gateway instance.
#
# Usage: provision_attendee_key.sh <attendee_id>
set -euo pipefail
cd "$(dirname "$0")/.."
source common.sh
require_config "$(pwd)/config.env"

ATTENDEE_ID="${1:?Usage: provision_attendee_key.sh <attendee_id>}"
PRODUCT_ID="attendee-${ATTENDEE_ID}"

log "Creating product $PRODUCT_ID"
az apim product create \
  --resource-group "$HUB_RESOURCE_GROUP" \
  --service-name "$APIM_NAME" \
  --product-id "$PRODUCT_ID" \
  --product-name "Attendee ${ATTENDEE_ID}" \
  --subscription-required true \
  --approval-required false \
  --state published \
  --output none

az apim product api add \
  --resource-group "$HUB_RESOURCE_GROUP" \
  --service-name "$APIM_NAME" \
  --product-id "$PRODUCT_ID" \
  --api-id foundry-models \
  --output none

# Per-attendee rate limit: caps one attendee's calls without touching
# anyone else's product. Lab 30 has attendees tune these numbers
# themselves; this is a safe starting point.
POLICY_XML=$(cat <<EOF
<policies>
  <inbound>
    <base />
    <rate-limit-by-key calls="60" renewal-period="60"
      counter-key="@(context.Subscription.Id)" />
    <quota-by-key calls="2000" renewal-period="86400"
      counter-key="@(context.Subscription.Id)" />
  </inbound>
  <backend><base /></backend>
  <outbound><base /></outbound>
  <on-error><base /></on-error>
</policies>
EOF
)

log "Applying rate-limit policy to $PRODUCT_ID"
az apim product api policy create \
  --resource-group "$HUB_RESOURCE_GROUP" \
  --service-name "$APIM_NAME" \
  --product-id "$PRODUCT_ID" \
  --format rawxml \
  --value "$POLICY_XML" \
  --output none

log "Creating subscription key for $ATTENDEE_ID"
az apim subscription create \
  --resource-group "$HUB_RESOURCE_GROUP" \
  --service-name "$APIM_NAME" \
  --sid "sub-${ATTENDEE_ID}" \
  --product-id "$PRODUCT_ID" \
  --display-name "Attendee ${ATTENDEE_ID}" \
  --output none

KEY=$(az apim subscription show \
  --resource-group "$HUB_RESOURCE_GROUP" \
  --service-name "$APIM_NAME" \
  --sid "sub-${ATTENDEE_ID}" \
  --query primaryKey -o tsv)

log "Key ready for $ATTENDEE_ID (hand this to them out of band, not over chat)"
echo "$KEY"
