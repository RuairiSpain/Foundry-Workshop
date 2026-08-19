#!/usr/bin/env bash
# Deletes the whole hub resource group: the hub, the router deployment,
# every attendee project, the Cosmos DB account, and the gateway. Run
# this after the workshop — nothing here scales to zero on its own, and
# the gateway and Cosmos DB both bill while they exist.
#
# Deleting the resource group is enough. Azure RBAC role assignments
# and Cosmos DB role assignments are deleted along with the resources
# they're scoped to, so there's nothing to clean up separately.
set -euo pipefail
cd "$(dirname "$0")"
source common.sh
require_config "$(pwd)/config.env"

read -r -p "Delete resource group $HUB_RESOURCE_GROUP and everything in it? [y/N] " CONFIRM
if [[ "$CONFIRM" != "y" && "$CONFIRM" != "Y" ]]; then
  log "Aborted"
  exit 0
fi

log "Deleting $HUB_RESOURCE_GROUP (runs in the background on Azure's side)"
az group delete --name "$HUB_RESOURCE_GROUP" --yes --no-wait

log "Delete requested. Check progress with: az group show --name $HUB_RESOURCE_GROUP"
