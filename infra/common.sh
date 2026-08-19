#!/usr/bin/env bash
# Shared helpers for the infra scripts. Source this after config.env:
#   source "$(dirname "$0")/../common.sh"
set -euo pipefail

log() {
  echo "[$(date +%H:%M:%S)] $*" >&2
}

require_config() {
  # Fail fast with a clear message instead of a mid-script az error,
  # since a missing config.env otherwise fails on whichever variable
  # the script happens to use first.
  local config_path="$1"
  if [[ ! -f "$config_path" ]]; then
    echo "Missing $config_path. Copy config.env.example and fill it in." >&2
    exit 1
  fi
  # shellcheck disable=SC1090
  source "$config_path"
  az account set --subscription "$SUBSCRIPTION_ID"
}

resource_group_exists() {
  az group show --name "$1" &>/dev/null
}
