#!/usr/bin/env bash
set -euo pipefail

MERMAID_VERSION="${MERMAID_VERSION:-11.15.0}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET_DIR="${ROOT_DIR}/vendor/mermaid"

rm -rf "${TARGET_DIR}"
mkdir -p "${TARGET_DIR}"

npm install --no-save "mermaid@${MERMAID_VERSION}"
cp -R "${ROOT_DIR}/node_modules/mermaid/dist" "${TARGET_DIR}/dist"

echo "Installed Mermaid ${MERMAID_VERSION} to ${TARGET_DIR}/dist"
