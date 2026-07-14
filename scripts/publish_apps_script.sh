#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

DESCRIPTION="${1:-GLA dashboard update $(date -u +%Y-%m-%dT%H:%M:%SZ)}"
DEPLOYMENT_FILE=".apps-script-deployment-id"

if [[ ! -f ".clasp.json" ]]; then
  echo "Missing .clasp.json."
  exit 1
fi

if [[ ! -f "$DEPLOYMENT_FILE" ]]; then
  echo "Missing $DEPLOYMENT_FILE."
  exit 1
fi

DEPLOYMENT_ID="$(tr -d '[:space:]' < "$DEPLOYMENT_FILE")"

echo "Uploading dashboard files to Apps Script..."
clasp push --force

echo "Creating a new Apps Script version..."
VERSION_OUTPUT="$(
  clasp create-version "$DESCRIPTION" 2>/dev/null ||
  clasp version "$DESCRIPTION"
)"

echo "$VERSION_OUTPUT"

VERSION="$(
  printf '%s\n' "$VERSION_OUTPUT" |
  grep -oE '[0-9]+' |
  tail -1
)"

if [[ -z "$VERSION" ]]; then
  echo "Could not determine the new version number."
  exit 1
fi

echo "Updating the employee web-app deployment..."

if clasp update-deployment "$DEPLOYMENT_ID" \
  --versionNumber "$VERSION" \
  --description "$DESCRIPTION"
then
  :
else
  echo "Trying the compatible deployment command..."
  clasp deploy \
    -i "$DEPLOYMENT_ID" \
    -V "$VERSION" \
    -d "$DESCRIPTION"
fi

echo
echo "Published Apps Script version $VERSION."
echo "The employee dashboard URL remains unchanged."
