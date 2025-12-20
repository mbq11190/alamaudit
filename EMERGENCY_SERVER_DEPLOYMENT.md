# 🚨 EMERGENCY FIX - Server Using Old Code

## Problem Identified

Your **production server is running OLD CODE** from commit `6936a58`:

```
Server Path: /extra-addons/alamaudit.git-6936a58556428/
Current HEAD: a9275f9 (latest)
```

The server still has the broken line:
```python
@api.depends('audit_id', 'audit_id.id')  # ❌ OLD CODE ON SERVER
```

## ✅ SOLUTION: Deploy Latest Code to Server

### Option 1: Git Pull on Server (RECOMMENDED)

```bash
# SSH into your server
ssh user@auditwise.thinkoptimise.com

# Navigate to addon directory
cd /var/odoo/auditwise.thinkoptimise.com/extra-addons/alamaudit.git-6936a58556428

# Pull latest changes
git fetch origin
git pull origin main

# Verify the fix is present
grep -n "@api.depends.*audit_id.*id" qaco_planning_phase/models/planning_p2_entity.py
# Expected: No matches (empty output)

# Restart Odoo service
sudo systemctl restart odoo
# OR
sudo service odoo restart
```

### Option 2: Manual File Update (QUICK FIX)

If Git pull doesn't work, manually update the file on server:

```bash
# SSH into server
ssh user@auditwise.thinkoptimise.com

# Edit the file
nano /var/odoo/auditwise.thinkoptimise.com/extra-addons/alamaudit.git-6936a58556428/qaco_planning_phase/models/planning_p2_entity.py

# Find line 201 and change:
# FROM: @api.depends('audit_id', 'audit_id.id')
# TO:   @api.depends('audit_id')

# Save and exit (Ctrl+X, Y, Enter)

# Restart Odoo
sudo systemctl restart odoo
```

### Option 3: Redeploy via Deployment System

If you use a deployment system (Ansible, Docker, etc.):

```bash
# Trigger redeployment with latest code
# (Command depends on your deployment system)
```

## 🔍 Verification After Fix

```bash
# Check Odoo logs
tail -f /var/log/odoo/odoo.log

# Watch for:
# ✅ "Registry loaded for auditwise.thinkoptimise.com" (no errors)
# ✅ No "NotImplementedError: Compute method cannot depend on field 'id'"
# ✅ No "KeyError: 'auditwise.thinkoptimise.com'"
```

## 📊 Server vs Local Comparison

| Location | File State | @api.depends Status |
|----------|------------|---------------------|
| **Local** (Windows) | ✅ Fixed | `@api.depends('audit_id')` |
| **Server** (Linux) | ❌ OLD | `@api.depends('audit_id', 'audit_id.id')` |
| **Git HEAD** | ✅ Fixed | Commit `a9275f9` |

## ⚠️ Why This Happened

The server addon path shows:
```
alamaudit.git-6936a58556428
```

This is likely an **old Git checkout** that hasn't been updated. Your local development has the fix, but the server needs to pull the latest changes.

## 🎯 Expected Result After Fix

Once you deploy the latest code and restart Odoo:

```
✅ Registry loads successfully
✅ Zero KeyError messages
✅ Zero NotImplementedError messages  
✅ Cron jobs run normally
✅ Planning P-2 page accessible
```

## 🚀 Quick Deploy Commands (Copy-Paste)

```bash
# Complete deployment sequence
ssh user@auditwise.thinkoptimise.com << 'EOF'
cd /var/odoo/auditwise.thinkoptimise.com/extra-addons/alamaudit.git-6936a58556428
git pull origin main
sudo systemctl restart odoo
sleep 5
sudo tail -n 50 /var/log/odoo/odoo.log | grep -E "ERROR|Registry loaded"
EOF
```

## 📞 If Git Pull Fails

If you get errors like:
- `fatal: not a git repository`
- `Permission denied`
- `Could not resolve host`

Then the server deployment uses a **copy** of the code, not a Git checkout. In that case:

1. Contact your DevOps team, OR
2. Use manual file edit (Option 2 above), OR
3. Redeploy entire module from latest Git commit

---

**Action Required**: Deploy latest code to production server NOW to eliminate the registry crash.
