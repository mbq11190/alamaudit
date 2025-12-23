#!/usr/bin/env bash
set -eu
if [ "$#" -lt 1 ]; then
  echo "Usage: $0 <db_name>"
  exit 2
fi
DB=$1
OUT=/tmp/orphan_metadata_${DB}.txt

echo "-- ir_model entries --" > "$OUT"
sudo -u postgres psql -d "$DB" -c "SELECT id, model, name FROM ir_model ORDER BY model;" >> "$OUT"

echo "\n-- ir_actions_server referencing missing models --" >> "$OUT"
sudo -u postgres psql -d "$DB" -c "SELECT id, name, model FROM ir_actions_server WHERE model NOT IN (SELECT model FROM ir_model);" >> "$OUT"

echo "\n-- ir_cron referencing missing models --" >> "$OUT"
sudo -u postgres psql -d "$DB" -c "SELECT id, name, model FROM ir_cron WHERE model NOT IN (SELECT model FROM ir_model);" >> "$OUT"

echo "Report written to $OUT"
