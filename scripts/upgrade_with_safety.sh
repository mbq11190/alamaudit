#!/usr/bin/env bash
set -euo pipefail

# Small safety wrapper to perform the common remediation/upgrade steps for qaco_client_onboarding
# Usage: ./scripts/upgrade_with_safety.sh [--confirm]
# If DB_NAME env var is set, the script will run the odoo upgrade at the end.

echo "[info] Starting safe upgrade helper script"
ROOT_DIR=$(cd "$(dirname "$0")/.." && pwd)
cd "$ROOT_DIR"

# 1) Backup critical view file
VIEW="qaco_client_onboarding/views/client_onboarding_form.xml"
if [ -f "$VIEW" ]; then
  BACKUP="$VIEW.bak.$(date +%s)"
  echo "[info] Backing up $VIEW -> $BACKUP"
  cp "$VIEW" "$BACKUP"
else
  echo "[warn] Expected view file not found: $VIEW" >&2
fi

# 2) Fix self-closing heading labels to be explicit content labels
# Using perl for a conservative replacement of patterns like:
#   <label string="Title"/>
# to
#   <label class="o_form_label">Title</label>
echo "[info] Applying XML heading fix (self-closing -> content label)"
perl -0777 -pe 's/<label\s+string=("|\')([^"\']+)\1\s*\/>/<label class="o_form_label">$2<\/label>/gs' -i "$VIEW"

# 3) Run static checks
echo "[info] Running label checker (will fail if problems remain)"
python3 scripts/check_view_labels.py || { echo "[error] Label checker failed"; exit 1; }

echo "[info] Running SCSS static checks"
python3 scripts/check_scss.py || { echo "[error] SCSS checks failed"; exit 1; }

echo "[info] Running accessibility checks"
python3 scripts/check_view_accessibility.py || { echo "[error] Accessibility checks failed"; exit 1; }

echo "[info] Running full repository checks"
python3 scripts/check_all.py || { echo "[error] General checks failed"; exit 1; }

# 4) Clear web assets (dry-run unless --confirm passed)
CONFIRM=0
if [ "${1:-}" = "--confirm" ]; then
  CONFIRM=1
fi
if [ $CONFIRM -eq 1 ]; then
  echo "[info] Clearing web assets (confirmed)"
  python3 scripts/clear_web_assets.py --confirm || true
else
  echo "[info] Dry-run: to actually clear assets, re-run with --confirm"
  python3 scripts/clear_web_assets.py || true
fi

# 5) Optional: run the Odoo upgrade (requires DB env vars)
if [ -n "${DB_NAME:-}" ]; then
  echo "[info] Running Odoo upgrade for $DB_NAME"
  # Note: ensure odoo-bin is available in PATH and the runtime environment is correct
  odoo-bin -d "$DB_NAME" -u qaco_client_onboarding --stop-after-init --log-level=debug || { echo "[error] Odoo upgrade command failed"; exit 1; }
else
  echo "[info] DB_NAME not set; skipping automatic odoo upgrade. Export DB_NAME and re-run this script to perform the upgrade."
fi

echo "[success] Safe upgrade helper finished"
exit 0
