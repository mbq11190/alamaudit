#!/usr/bin/env bash
# deploy_maintenance.sh
# Usage: sudo ./scripts/deploy_maintenance.sh <target_path> (example: /srv/www/maintenance/maintenance.html)
TARGET=${1:-}
if [[ -z "$TARGET" ]]; then
  echo "Usage: $0 <target_path>"
  exit 2
fi
if [[ ! -f docs/maintenance/maintenance.html ]]; then
  echo "Maintenance HTML not found at docs/maintenance/maintenance.html"
  exit 1
fi
sudo mkdir -p "$(dirname "$TARGET")"
sudo cp docs/maintenance/maintenance.html "$TARGET"
sudo chown root:root "$TARGET"
if command -v systemctl >/dev/null 2>&1 && systemctl is-active --quiet nginx; then
  echo "Reloading nginx"
  sudo systemctl reload nginx || echo "nginx reload failed"
else
  echo "Nginx not running; copy is complete"
fi
echo "Maintenance deployed to $TARGET"