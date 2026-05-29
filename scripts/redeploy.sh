#!/usr/bin/env bash

set -Eeuo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd -- "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT_DIR"

# Farben
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo ""
echo -e "${GREEN}   Meme-Bot - Redeploy${NC}"
echo ""

# Docker Check
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Docker nicht installiert!${NC}"
    exit 1
fi

if ! docker compose version &> /dev/null; then
    echo -e "${RED}Docker Compose Plugin nicht installiert!${NC}"
    exit 1
fi

# .env Check
if [ ! -f "$ROOT_DIR/.env" ]; then
    echo -e "${RED}.env fehlt!${NC}"
    echo -e "Anlegen mit: ${YELLOW}cp .env.example .env${NC} und Tokens eintragen."
    exit 1
fi

# Neuesten Code holen (nur Fast-Forward; bricht ab, wenn lokal divergiert)
echo -e "${YELLOW}Hole neuesten Code (git pull --ff-only)...${NC}"
git pull --ff-only

# Image neu bauen + Container neu starten
echo -e "${YELLOW}Baue Image und starte Meme-Bot neu...${NC}"
docker compose up -d --build

# Status
echo ""
docker compose ps
echo ""
echo -e "${GREEN}Redeploy fertig. Meme-Bot läuft mit dem neuesten Stand.${NC}"
echo -e "Logs ansehen: ${GREEN}./scripts/logs.sh${NC}"
echo ""
