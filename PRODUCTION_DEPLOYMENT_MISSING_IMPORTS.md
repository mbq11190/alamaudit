# PRODUCTION DEPLOYMENT: Fix NameError - Missing Odoo Imports
## Issue Resolved
- **Error**: NameError: name 'models' is not defined in planning_p7_fraud.py and planning_p10_related_parties.py
- **Root Cause**: Missing `from odoo import api, fields, models` imports in P-tab model files
- **Impact**: Odoo registry fails to load, preventing application startup

## Local Fixes Applied
✅ Added missing Odoo imports to planning_p7_fraud.py
✅ Added missing Odoo imports to planning_p10_related_parties.py
✅ Added proper docstring headers for consistency
✅ Committed changes: Latest commit ready for deployment

## Deployment Instructions
Execute these commands on the production server:

```bash
# Navigate to the alamaudit repository
cd /var/odoo/auditwise.thinkoptimise.com/extra-addons/alamaudit

# Pull latest changes from main branch
git pull origin main

# Restart Odoo service
sudo systemctl restart odoo

# Monitor logs for successful startup
sudo tail -f /var/log/odoo/odoo-server.log
```

## Verification Steps
1. Check Odoo web interface loads without errors
2. Verify Planning Phase module loads correctly
3. Test P-7 Fraud Risk Assessment tab functionality
4. Test P-10 Related Parties tab functionality
5. Confirm cron jobs execute without exceptions

## Expected Log Output
After restart, you should see:
```
INFO ... odoo.modules.loading: loading qaco_planning_phase/models/planning_p7_fraud.py
INFO ... odoo.modules.loading: loading qaco_planning_phase/models/planning_p10_related_parties.py
INFO ... odoo.modules.registry: Registry loaded successfully
```

## Rollback Plan
If issues persist:
```bash
# Revert to previous commit
git reset --hard HEAD~1
sudo systemctl restart odoo
```

## Commit Details
- **Latest Commit**: Includes fixes for missing imports
- **Files Modified**: planning_p7_fraud.py, planning_p10_related_parties.py
- **Previous Issues**: All syntax errors and NotImplementedError fixes already deployed locally</content>
<parameter name="filePath">c:\Users\HP\Documents\GitHub\alamaudit\PRODUCTION_DEPLOYMENT_MISSING_IMPORTS.md