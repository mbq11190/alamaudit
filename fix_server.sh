#!/bin/bash
# Run this script: ssh root@139.84.166.37 'bash -s' < fix_server.sh

set -e

echo "=== Fixing Odoo Server Issues ==="
echo ""

# Navigate to module directory
cd /var/odoo/auditwise.thinkoptimise.com/extra-addons/alamaudit.git-*

echo "Step 1: Updating code from GitHub..."
git fetch origin
git reset --hard origin/main
git pull origin main
echo "✓ Code updated to latest version"
echo ""

echo "Step 2: Clearing Python cache..."
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete
echo "✓ Python cache cleared"
echo ""

echo "Step 3: Restarting Odoo..."
systemctl stop odoo
sleep 3
systemctl start odoo
sleep 5
echo "✓ Odoo restarted"
echo ""

echo "Step 4: Checking status..."
systemctl status odoo --no-pager | head -15
echo ""

echo "=== Fix Applied ==="
echo "Please test: https://auditwise.thinkoptimise.com"
echo ""
echo "If still having issues, check logs with:"
echo "  journalctl -u odoo -n 100 --no-pager"
