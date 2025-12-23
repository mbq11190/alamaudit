#!/usr/bin/env bash
# Emergency containment: safely mark a module as to-remove so Odoo can boot.
# Usage: sudo ./scripts/containment_disable_module.sh <db> <module_name>
set -euo pipefail
DB=${1:-}
MODULE=${2:-}
if [[ -z "$DB" || -z "$MODULE" ]]; then
  echo "Usage: $0 <db> <module_name>"
  exit 2
fi

echo "Marking module '$MODULE' as to_remove in database $DB"
sudo -u postgres psql -d "$DB" -c "UPDATE ir_module_module SET state='to remove' WHERE name = '$MODULE';"

echo "Optionally, to mark all modules installed in the last 7 days as to_remove (use with caution):"
echo "sudo -u postgres psql -d \"$DB\" -c \"UPDATE ir_module_module SET state='to remove' WHERE create_date > now() - INTERVAL '7 days';\""

echo "After this, restart Odoo service (systemd example):"
echo "sudo systemctl restart odoo"

echo "Check logs: sudo journalctl -u odoo -f"
