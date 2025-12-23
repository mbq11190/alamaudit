#!/usr/bin/env bash
# Safe wrapper to run generate_disable_and_optimize.sql in DRY-RUN or APPLY mode
# Usage: ./scripts/db_optimize.sh --db <dbname> [--apply] [--psql psql]

set -eu
DB=""
PSQL="psql"
APPLY=0
SQL_FILE="$(pwd)/scripts/generate_disable_and_optimize.sql"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --db) DB="$2"; shift 2;;
    --psql) PSQL="$2"; shift 2;;
    --apply) APPLY=1; shift;;
    -h|--help) echo "Usage: $0 --db <dbname> [--apply] [--psql psql]"; exit 0;;
    *) echo "Unknown arg: $1"; exit 1;;
  esac
done

if [[ -z "$DB" ]]; then
  echo "Error: --db <dbname> is required" >&2
  exit 2
fi

echo "DB Optimize wrapper (DRY-RUN by default). DB=$DB"

echo "Step 1: Ensure backup exists (creating one now)"
sudo -u postgres pg_dump "$DB" | gzip > "/tmp/${DB}_preopt_$(date +%Y%m%d_%H%M%S).sql.gz"

if [[ $APPLY -eq 0 ]]; then
  echo "DRY-RUN mode: printing SQL to stdout (no changes will be applied)"
  sed -n '1,400p' "$SQL_FILE"
  echo "\nTo apply, re-run with --apply after reviewing the SQL and confirming backups.";
  exit 0
fi

# Apply mode (careful)
read -p "Type YES to APPLY the optimization SQL to DB $DB: " confirm
if [[ "$confirm" != "YES" ]]; then
  echo "Aborted by user"; exit 1
fi

echo "Applying SQL to DB $DB"
sudo -u postgres psql -d "$DB" -f "$SQL_FILE"

echo "Optimization SQL applied. Recommend verifying and monitoring logs."
