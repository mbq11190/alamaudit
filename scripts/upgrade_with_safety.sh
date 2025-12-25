#!/usr/bin/env bash
set -euo pipefail

# Small safety wrapper to perform the common remediation/upgrade steps for qaco_client_onboarding
# Usage: ./scripts/upgrade_with_safety.sh [--confirm]
# If DB_NAME env var is set, the script will run the odoo upgrade at the end.

echo "[info] Starting safe upgrade helper script"
ROOT_DIR=$(cd "$(dirname "$0")/.." && pwd)
cd "$ROOT_DIR"

# Prefer Python from project venv if available, else system python
PYTHON=""
if [ -x "$ROOT_DIR/.venv/bin/python" ]; then
  PYTHON="$ROOT_DIR/.venv/bin/python"
elif [ -x "$ROOT_DIR/.venv/Scripts/python.exe" ]; then
  PYTHON="$ROOT_DIR/.venv/Scripts/python.exe"
elif command -v python3 >/dev/null 2>&1; then
  PYTHON=python3
elif command -v python >/dev/null 2>&1; then
  PYTHON=python
else
  echo "[error] No python interpreter found (python3/python or .venv). Install Python or activate the venv." >&2
  exit 2
fi
echo "[info] Using python: $PYTHON"

# Keep a backup name variable so we can restore on failure
VIEW="qaco_client_onboarding/views/client_onboarding_form.xml"
BACKUP=""
if [ -f "$VIEW" ]; then
  BACKUP="$VIEW.bak.$(date +%s)"
  echo "[info] Backing up $VIEW -> $BACKUP"
  cp "$VIEW" "$BACKUP"
else
  echo "[warn] Expected view file not found: $VIEW" >&2
fi

# Restore backup on unexpected failure
trap 'rc=$?; if [ $rc -ne 0 ]; then echo "[error] Script failed (rc=$rc)"; if [ -n "${BACKUP:-}" ] && [ -f "$BACKUP" ]; then echo "[info] Restoring $VIEW from $BACKUP"; cp "$BACKUP" "$VIEW"; fi; fi; exit $rc' ERR

# 2) Fix self-closing heading labels to be explicit content labels, only if patterns exist
if [ -f "$VIEW" ] && grep -q '<label ' "$VIEW" && grep -q '/>' "$VIEW"; then
  echo "[info] Applying XML heading fix (self-closing -> content label)"
  perl -0777 -pe 's/<label\s+string=("|\')([^"\']+)\1\s*\/>/<label class="o_form_label">$2<\/label>/gs' -i "$VIEW"
else
  echo "[info] No self-closing label patterns found in $VIEW; skipping xml fix"
fi

# 3) Run static checks
echo "[info] Running label checker (will fail if problems remain)"
"$PYTHON" scripts/check_view_labels.py || { echo "[error] Label checker failed"; exit 1; }

echo "[info] Running SCSS static checks"
"$PYTHON" scripts/check_scss.py || { echo "[error] SCSS checks failed"; exit 1; }

echo "[info] Running accessibility checks"
"$PYTHON" scripts/check_view_accessibility.py || { echo "[error] Accessibility checks failed"; exit 1; }

echo "[info] Running full repository checks"
"$PYTHON" scripts/check_all.py || { echo "[error] General checks failed"; exit 1; }

# 4) Clear web assets (dry-run unless --confirm passed)
CONFIRM=0
if [ "${1:-}" = "--confirm" ]; then
  CONFIRM=1
fi
if [ $CONFIRM -eq 1 ]; then
  echo "[info] Clearing web assets (confirmed)"
  "$PYTHON" scripts/clear_web_assets.py --confirm || true
else
  echo "[info] Dry-run: to actually clear assets, re-run with --confirm"
  "$PYTHON" scripts/clear_web_assets.py || true
fi

# 5) Optional: run the Odoo upgrade (requires DB env vars)
if [ -n "${DB_NAME:-}" ]; then
  echo "[info] Running Odoo upgrade for $DB_NAME"
  ODOO_BIN="${ODOO_BIN:-$(command -v odoo-bin || true)}"
  if [ -z "$ODOO_BIN" ]; then
    echo "[error] odoo-bin not found in PATH. Set ODOO_BIN to the path to your odoo-bin executable or ensure it is in PATH." >&2
    exit 1
  fi
  "$ODOO_BIN" -d "$DB_NAME" -u qaco_client_onboarding --stop-after-init --log-level=debug || { echo "[error] Odoo upgrade command failed"; exit 1; }
else
  echo "[info] DB_NAME not set; skipping automatic odoo upgrade. Export DB_NAME and re-run this script to perform the upgrade."
fi

echo "[success] Safe upgrade helper finished"
exit 0
