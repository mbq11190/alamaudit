#!/bin/bash
# Deployment script for production server
# Run this on the production server after SSH'ing in

set -e  # Exit on error

echo "=== Alamaudit Deployment Script ==="
echo ""

# Navigate to module directory
MODULE_DIR="/var/odoo/auditwise.thinkoptimise.com/extra-addons/alamaudit.git-69477af08ae83"
cd "$MODULE_DIR"

echo "1. Pulling latest code from GitHub..."
git fetch origin
git reset --hard origin/main
echo "✓ Code updated"
echo ""

echo "2. Clearing Python bytecode cache..."
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete
echo "✓ Cache cleared"
echo ""

echo "3. Stopping Odoo service..."
sudo systemctl stop odoo
sleep 2
echo "✓ Odoo stopped"
echo ""

echo "4. Starting Odoo service..."
sudo systemctl start odoo
sleep 5
echo "✓ Odoo started"
echo ""

echo "5. Checking Odoo status..."
sudo systemctl status odoo --no-pager -l | head -20
echo ""

echo "=== Deployment Complete ==="
echo ""
echo "Next steps:"
echo "1. Open browser and navigate to: https://auditwise.thinkoptimise.com"
echo "2. Login with your credentials"
echo "3. Go to Apps menu"
echo "4. Search for 'qaco' modules"
echo "5. Click 'Upgrade' on each module if needed"
echo ""
echo "If you still see issues:"
echo "  - Check logs: sudo journalctl -u odoo -n 100 --no-pager"
echo "  - Check Odoo log file for detailed errors"
