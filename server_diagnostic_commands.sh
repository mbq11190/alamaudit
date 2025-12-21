#!/bin/bash
# Server Diagnostic Commands for 139.84.166.37
# Run these commands after SSH'ing into the server

echo "=========================================="
echo "1. CHECK CURRENT GIT COMMIT"
echo "=========================================="
cd /var/odoo/auditwise.thinkoptimise.com/alamaudit* 2>/dev/null || cd /var/odoo/*/alamaudit* 2>/dev/null
pwd
git log -1 --oneline
echo ""
echo "Expected: d431bc9 fix: Remove store=True from final 2 related fields"
echo ""

echo "=========================================="
echo "2. CHECK FOR PYTHON CACHE FILES"
echo "=========================================="
find . -type d -name "__pycache__" | head -20
find . -name "*.pyc" | head -20
echo ""

echo "=========================================="
echo "3. VERIFY FIXED FILES CONTENT"
echo "=========================================="
echo "--- Checking planning_p6_risk.py line 496 ---"
grep -n "combined_rmm.*store" qaco_planning_phase/models/planning_p6_risk.py || echo "Pattern not found"
echo ""
echo "--- Checking planning_p2_entity.py line 261 ---"
grep -n "legal_name.*store" qaco_planning_phase/models/planning_p2_entity.py || echo "Pattern not found"
echo ""

echo "=========================================="
echo "4. SEARCH FOR ANY REMAINING store=True"
echo "=========================================="
grep -r "related.*store.*True" qaco_*/models/*.py 2>/dev/null | grep -v ".pyc" || echo "No instances found (GOOD!)"
echo ""

echo "=========================================="
echo "5. CHECK ODOO PROCESS STATUS"
echo "=========================================="
ps aux | grep odoo | grep -v grep
echo ""

echo "=========================================="
echo "6. CHECK RECENT ODOO LOGS"
echo "=========================================="
tail -50 /var/log/odoo/odoo.log 2>/dev/null || tail -50 /var/log/odoo-server.log 2>/dev/null || echo "Log file not found at standard location"
echo ""

echo "=========================================="
echo "RECOMMENDED ACTIONS:"
echo "=========================================="
echo "If commit is NOT d431bc9:"
echo "  → Run: git pull origin main"
echo ""
echo "If Python cache exists:"
echo "  → Run: find . -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null"
echo "  → Run: find . -name '*.pyc' -delete"
echo ""
echo "If store=True still exists in files:"
echo "  → The deployment didn't pick up the changes"
echo "  → Re-run git pull and check file contents manually"
echo ""
echo "After fixes, restart Odoo:"
echo "  → systemctl restart odoo (or your specific service name)"
echo "  → OR: odoo-bin -d auditwise.thinkoptimise.com -u qaco_planning_phase --stop-after-init"
