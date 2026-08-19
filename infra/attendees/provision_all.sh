#!/usr/bin/env bash
# Runs provision_attendee.sh for every row in a roster CSV and writes
# the results (project name, gateway key) to a handout file. Run this
# after hub/deploy_hub.sh, cosmos/deploy_cosmos.sh, and
# gateway/deploy_gateway.sh have all finished.
#
# Usage: provision_all.sh <roster.csv> [output.csv]
set -euo pipefail
cd "$(dirname "$0")"

ROSTER="${1:?Usage: provision_all.sh <roster.csv> [output.csv]}"
OUTPUT="${2:-provisioned.csv}"

if [[ ! -f "$ROSTER" ]]; then
  echo "Roster file not found: $ROSTER" >&2
  exit 1
fi

echo "attendee_id,project_name,gateway_key" > "$OUTPUT"

# tail +2 skips the header row.
tail -n +2 "$ROSTER" | while IFS=, read -r attendee_id principal_id; do
  [[ -z "$attendee_id" ]] && continue
  ./provision_attendee.sh "$attendee_id" "$principal_id" >> "$OUTPUT"
done

echo "Done. Per-attendee handout written to $OUTPUT — distribute each row individually, not as one shared file."
