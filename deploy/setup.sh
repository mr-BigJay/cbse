#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

if [[ ! -f .env ]]; then
  echo "Copy .env.example to .env and edit secrets first."
  exit 1
fi

docker compose build
docker compose up -d postgres
echo "Waiting for PostgreSQL..."
sleep 5
docker compose up -d

echo "Stack started. Configure DNS for DOMAIN and visit https://$DOMAIN"
