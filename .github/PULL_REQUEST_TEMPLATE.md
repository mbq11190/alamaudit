## Summary
This PR contains emergency recovery scripts, maintenance deployment scripts, and diagnostic helpers to safely contain registry-breaking errors and provide a friendly maintenance page.

## What it includes
- scripts/emergency_contain_and_maintain.sh — backup, disable modules, deploy maintenance page, restart Odoo
- scripts/deploy_maintenance.sh — copy maintenance HTML and reload nginx
- docs/EMERGENCY_RECOVERY.md — step-by-step recovery guide
- docs/maintenance/maintenance.html — friendly maintenance page
- scripts/generate_inverse_fix.py — helper to generate minimal patch suggestions

## How to test
1. Review the scripts for your environment
2. Run in a safe staging environment (do NOT run on production without a backup)
3. Confirm the maintenance page deploys and Odoo restarts are successful

## Rollout/Upgrade plan
- Use the scripts only after taking a DB backup
- Prefer disabling a single suspect module rather than bulk operations

## Notes
- These scripts are interactive and require explicit YES confirmation before performing destructive changes
- If you want me to open the PR to the upstream repository with reviewers, let me know the reviewers' GitHub handles.