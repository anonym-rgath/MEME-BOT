#!/usr/bin/env bash

set -Eeuo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd -- "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT_DIR"

# Meme-Bot-Logs anzeigen
# ======================

echo "Zeige Meme-Bot-Logs (STRG+C zum Beenden)..."
echo ""

docker compose logs -f "$@"
