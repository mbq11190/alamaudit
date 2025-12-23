#!/usr/bin/env bash
# Safe orchestrator for Odoo registry & metadata diagnostics and dry-run fix generation
# Usage: ./scripts/safe_odoo_fix.sh --db <dbname> [--psql psql] [--out dryrun.sql] [--apply]

set -eu
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SCRIPTS_DIR="$ROOT/scripts"
DB=""
PSQL="psql"
OUT_FILE="$SCRIPTS_DIR/dryrun_suggestions.sql"
APPLY=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --db) DB="$2"; shift 2;;
    --psql) PSQL="$2"; shift 2;;
    --out) OUT_FILE="$2"; shift 2;;
    --apply) APPLY=1; shift;;
    -h|--help) echo "Usage: $0 [--db <dbname>] [--psql psql] [--out file] [--apply]"; exit 0;;
    *) echo "Unknown arg: $1"; exit 1;;
  esac
done

echo "Safe orchestrator starting... (DRY-RUN by default)"
mkdir -p "$SCRIPTS_DIR"

# Step 1: create DB dump if DB specified
if [[ -n "$DB" ]]; then
  echo "Creating DB dump to /tmp/${DB}_dump.sql (compressed)"
  sudo -u postgres pg_dump "$DB" | gzip > "/tmp/${DB}_dump.sql.gz"
  echo "DB dump created: /tmp/${DB}_dump.sql.gz"
fi

# Step 2: generate repo model list
echo "Generating repo model list..."
python3 "$SCRIPTS_DIR/compare_repo_models.py" > "$SCRIPTS_DIR/repo_models.txt"

# Step 3: gather DB evidence (if DB provided)
if [[ -n "$DB" ]]; then
  echo "Dumping DB model list..."
  sudo -u postgres psql -d "$DB" -c "COPY (SELECT model FROM ir_model ORDER BY model) TO STDOUT;" > "$SCRIPTS_DIR/db_models.txt"
  echo "Running orphan checks (queries)"
  sudo -u postgres psql -d "$DB" -f "$SCRIPTS_DIR/orphan_ir_model_checks.sql" > "$SCRIPTS_DIR/orphan_report.txt"
fi

# Step 4: run trace extractor if log present
if [[ -f "/tmp/upgrade-${DB}.log" ]]; then
  echo "Extracting first traceback from /tmp/upgrade-${DB}.log"
  python3 "$SCRIPTS_DIR/find_first_traceback.py" "/tmp/upgrade-${DB}.log" > "$SCRIPTS_DIR/first_traceback.txt" 2>/dev/null || true
fi

# Step 5: Generate dry-run SQL
echo "Generating dry-run SQL (non-destructive suggestions)"
if [[ -n "$DB" ]]; then
  python3 "$SCRIPTS_DIR/generate_dryrun_sql.py" --db "$DB" --psql "$PSQL" --out "$OUT_FILE"
else
  python3 "$SCRIPTS_DIR/generate_dryrun_sql.py" --out "$OUT_FILE"
fi

echo "DRY-RUN SQL ready: $OUT_FILE"

if [[ $APPLY -eq 1 ]]; then
  echo "-- APPLY flag detected --" 
  echo "WARNING: Apply will run the SQL in $OUT_FILE against DB=$DB. This may be destructive. Proceed only if you reviewed the file and have backups."
  read -p "Type YES to proceed: " confirm
  if [[ "$confirm" == "YES" ]]; then
    if [[ -z "$DB" ]]; then
      echo "DB not specified - cannot apply"; exit 1
    fi
    echo "Applying suggested SQL to DB (this will run commented statements as well; manual review recommended)"
    sudo -u postgres psql -d "$DB" -f "$OUT_FILE"
    echo "Apply complete"
  else
    echo "Apply aborted by user"
  fi
fi

# Summary output
echo "Summary files written to: $SCRIPTS_DIR"
ls -l "$SCRIPTS_DIR" | egrep -i 'repo_models|db_models|orphan_report|dryrun|first_traceback' || true

echo "Safe orchestrator finished (DRY-RUN). Review $OUT_FILE and scripts/dryrun_report.txt before applying any changes."
