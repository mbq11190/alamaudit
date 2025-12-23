#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 1 ]; then
  echo "Usage: $0 <db_name> [module1,module2,...]"
  exit 2
fi
DB="$1"
MODULES="${2:-qaco_client_onboarding,web_responsive}"
BACKUP_DIR="/tmp"
BACKUP="$BACKUP_DIR/${DB}-before-onboarding-fix.dump"
LOGFILE="/tmp/upgrade-${DB}.log"

echo "Backing up DB $DB to $BACKUP"
sudo -u postgres pg_dump -Fc -f "$BACKUP" "$DB"

echo "Stopping odoo service"
sudo systemctl stop odoo || true

echo "Pulling latest code on branch main (ensure you are on the correct branch)"
git fetch origin
if git rev-parse --abbrev-ref HEAD | grep -q "main"; then
  git pull origin main
else
  echo "Warning: you are not on main branch. Please ensure correct code is checked out."
fi

echo "Upgrading modules: $MODULES"
./odoo-bin -d "$DB" -u ${MODULES} --stop-after-init --log-level=info 2>&1 | tee "$LOGFILE"

# After upgrade, dump DB model list and compare to repo list
echo "Exporting DB model list to /tmp/db_models_${DB}.txt"
sudo -u postgres psql -d "$DB" -At -c "SELECT model FROM ir_model ORDER BY model;" > "/tmp/db_models_${DB}.txt" || true

# Generate repo model list
echo "Generating repo model list"
python scripts/compare_repo_models.py > "/tmp/repo_models_${DB}.txt"

# Diff the lists and emit summary
echo "Models present in DB but not in repo:"
comm -23 "/tmp/db_models_${DB}.txt" "/tmp/repo_models_${DB}.txt" | tee "/tmp/missing_in_repo_${DB}.txt" || true

echo "Checking upgrade logs for critical failures"
if grep -E "KeyError: 'onboarding_id'|Invalid field 'is_redirect_home'|Missing model" "$LOGFILE" -n ; then
  echo "ERROR: Detected issues in the upgrade log. Please inspect $LOGFILE"
  exit 3
fi

echo "Restarting odoo service"
sudo systemctl start odoo

echo "Upgrade finished successfully. Log at: $LOGFILE"
exit 0
