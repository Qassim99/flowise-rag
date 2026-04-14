#!/bin/bash

DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

if command -v podman &>/dev/null; then
  COMPOSE="podman compose"
elif command -v docker &>/dev/null; then
  COMPOSE="docker compose"
else
  echo "ERROR: Neither podman nor docker found"
  exit 1
fi

if [ "$1" = "--clean" ]; then
  echo "▶ Stopping containers and removing all volumes..."
  $COMPOSE down -v
  echo "✓ Everything removed (data deleted)"
else
  echo "▶ Stopping containers..."
  $COMPOSE down
  echo "✓ Stopped (data preserved)"
fi
