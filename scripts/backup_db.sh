#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")"/.. && pwd)"
DB_PATH="$ROOT_DIR/data/kanban.db"
BACKUP_DIR="$ROOT_DIR/backups"

mkdir -p "$BACKUP_DIR"

if [ ! -f "$DB_PATH" ]; then
  echo "No database found at $DB_PATH" >&2
  exit 1
fi

TS="$(date +%Y%m%d-%H%M%S)"
cp "$DB_PATH" "$BACKUP_DIR/kanban-$TS.db"
echo "Backup created: $BACKUP_DIR/kanban-$TS.db"