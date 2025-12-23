#!/usr/bin/env bash
# emergency_contain_and_maintain.sh
# Usage: sudo ./scripts/emergency_contain_and_maintain.sh <DB> [--disable-recent-days N] [--disable-module <module_name>] [--deploy-maintenance <target_path>]
# This script is interactive and will NOT run destructive commands without your confirmation.
set -euo pipefail
DB=${1:-}
if [[ -z "$DB" ]]; then
  echo "Usage: $0 <DB> [--disable-recent-days N] [--disable-module <module> ] [--deploy-maintenance <target_path>]"
  exit 2
fi

# Defaults
DISABLE_RECENT_DAYS=0
DISABLE_MODULE=""
DEPLOY_MAINTENANCE=""

while [[ $# -gt 0 ]]; do
  case "$2" in
    --disable-recent-days)
      DISABLE_RECENT_DAYS="$3"
      shift 2
      ;;
    --disable-module)
      DISABLE_MODULE="$3"
      shift 2
      ;;
    --deploy-maintenance)
      DEPLOY_MAINTENANCE="$3"
      shift 2
      ;;
    *) break ;;
  esac
done

# Confirm
echo "Emergency containment for DB: $DB"
if [[ $DISABLE_RECENT_DAYS -ne 0 ]]; then
  echo " - Will set state='to remove' for modules installed/updated in last $DISABLE_RECENT_DAYS days"
fi
if [[ -n "$DISABLE_MODULE" ]]; then
  echo " - Will set state='to remove' for module: $DISABLE_MODULE"
fi
if [[ -n "$DEPLOY_MAINTENANCE" ]]; then
  echo " - Will copy maintenance page to: $DEPLOY_MAINTENANCE"
fi

read -p "Proceed with the above steps? Type YES to continue: " CONFIRM
if [[ "$CONFIRM" != "YES" ]]; then
  echo "Aborting - not confirmed"
  exit 1
fi

# 1) Backup DB
BACKUP="/tmp/${DB}_backup_$(date +%Y%m%d_%H%M%S).sql"
echo "Creating DB backup: $BACKUP"
sudo -u postgres pg_dump "$DB" > "$BACKUP" || { echo "Backup failed"; exit 1; }

# 2) Disable modules (if requested)
if [[ -n "$DISABLE_MODULE" ]]; then
  echo "Disabling module: $DISABLE_MODULE"
  sudo -u postgres psql -d "$DB" -c "UPDATE ir_module_module SET state='to remove' WHERE name='$DISABLE_MODULE';"
fi
if [[ $DISABLE_RECENT_DAYS -gt 0 ]]; then
  echo "Disabling modules installed/updated in last $DISABLE_RECENT_DAYS days"
  sudo -u postgres psql -d "$DB" -c "UPDATE ir_module_module SET state='to remove' WHERE state='installed' AND (create_date > NOW() - INTERVAL '$DISABLE_RECENT_DAYS days' OR write_date > NOW() - INTERVAL '$DISABLE_RECENT_DAYS days');"
fi

# 3) Deploy maintenance page (optional)
if [[ -n "$DEPLOY_MAINTENANCE" ]]; then
  echo "Deploying maintenance page to $DEPLOY_MAINTENANCE"
  if [[ ! -f docs/maintenance/maintenance.html ]]; then
    echo "Maintenance page not found at docs/maintenance/maintenance.html"
  else
    sudo mkdir -p "$(dirname "$DEPLOY_MAINTENANCE")"
    sudo cp docs/maintenance/maintenance.html "$DEPLOY_MAINTENANCE"
    sudo chown root:root "$DEPLOY_MAINTENANCE"
    echo "Maintenance page copied. Reloading nginx (if present)"
    if command -v systemctl >/dev/null 2>&1 && systemctl is-active --quiet nginx; then
      sudo systemctl reload nginx || echo "nginx reload failed"
    else
      echo "No active nginx service found; skip reload"
    fi
  fi
fi

# 4) Restart Odoo
echo "Restarting Odoo service"
sudo systemctl restart odoo

# 5) Tail logs for a while
echo "Tailing Odoo logs (press Ctrl+C to stop)"
sudo journalctl -u odoo -f

echo "Emergency containment script finished (tailing stopped). Check logs for 'Registry loaded on db'"