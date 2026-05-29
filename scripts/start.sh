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
echo -e "${GREEN}   Meme-Bot - Start${NC}"
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

echo -e "${YELLOW}Baue und starte Meme-Bot...${NC}"
docker compose up -d --build

# Status
echo ""
docker compose ps
echo ""
echo -e "${GREEN}Meme-Bot läuft (Long-Polling, kein offener Port nötig).${NC}"
echo -e "Logs ansehen: ${GREEN}./scripts/logs.sh${NC}"
echo -e "Stoppen:      ${GREEN}./scripts/stop.sh${NC}"
echo ""
