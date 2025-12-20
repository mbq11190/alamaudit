# ODOO PRODUCTION DEPLOYMENT & TROUBLESHOOTING GUIDE
## Specific to auditwise.thinkoptimise.com - Missing Imports Fix

### **Current Issue**
- **Error**: NameError: name 'models' is not defined
- **Location**: planning_p7_fraud.py and planning_p10_related_parties.py
- **Impact**: Odoo registry fails to load, causing Internal Server Error
- **Status**: Fixed locally, ready for deployment

---

## **1. PRE-DEPLOYMENT CHECKS**

### Review Local Changes
```bash
cd /var/odoo/auditwise.thinkoptimise.com/extra-addons/alamaudit
git log --oneline -3
# Should show: 1348ba0 Fix missing Odoo imports...
```

### Validate Code Locally (if possible)
```bash
# Test Python syntax
python3 -m py_compile qaco_planning_phase/models/planning_p7_fraud.py
python3 -m py_compile qaco_planning_phase/models/planning_p10_related_parties.py
```

---

## **2. DEPLOYMENT EXECUTION**

### Pull Latest Changes
```bash
cd /var/odoo/auditwise.thinkoptimise.com/extra-addons/alamaudit
git pull origin main
```

### Check File Permissions
```bash
# Ensure Odoo user can read the files
sudo chown -R odoo:odoo /var/odoo/auditwise.thinkoptimise.com/extra-addons/alamaudit
sudo chmod -R 755 /var/odoo/auditwise.thinkoptimise.com/extra-addons/alamaudit
```

### Restart Odoo Service
```bash
sudo systemctl restart odoo
# Wait 30 seconds for startup
sleep 30
```

---

## **3. IMMEDIATE POST-DEPLOYMENT VERIFICATION**

### Check Service Status
```bash
sudo systemctl status odoo
# Should show: Active (running)
```

### Monitor Logs in Real-Time
```bash
sudo tail -f /var/log/odoo/odoo-server.log
# Look for:
# - "Registry loaded successfully"
# - No "NameError" or "ImportError"
# - Successful loading of qaco_planning_phase
```

### Test Web Interface
```bash
# Check if Odoo web interface loads
curl -I http://auditwise.thinkoptimise.com
# Should return HTTP 200 OK
```

---

## **4. RESOURCE & SYSTEM HEALTH CHECKS**

### Monitor System Resources
```bash
# CPU, Memory, Disk usage
top -b -n1 | head -20
df -h
free -m

# Network connections
netstat -tulpn | grep :8069  # Default Odoo port
```

### Check Database Connectivity
```bash
# Test PostgreSQL connection (if using psql)
sudo -u postgres psql -d auditwise -c "SELECT version();"

# Or check Odoo database connection in logs
grep -i "database" /var/log/odoo/odoo-server.log
```

---

## **5. DEPENDENCY & SERVICE VALIDATION**

### Verify Required Services
```bash
# PostgreSQL
sudo systemctl status postgresql

# Nginx/Apache (if used as reverse proxy)
sudo systemctl status nginx

# Check Odoo Python environment
sudo -u odoo python3 -c "import odoo; print('Odoo import successful')"
```

### Update Dependencies (if needed)
```bash
# As odoo user
sudo -u odoo pip3 install --upgrade pip
sudo -u odoo pip3 install -r requirements.txt  # If exists
```

---

## **6. APPLICATION-SPECIFIC TESTING**

### Test Planning Phase Module
```bash
# Check if modules load without errors
sudo -u odoo python3 -c "
import sys
sys.path.append('/var/odoo/auditwise.thinkoptimise.com/extra-addons')
try:
    from qaco_planning_phase.models import planning_p7_fraud, planning_p10_related_parties
    print('SUCCESS: All imports working')
except Exception as e:
    print(f'ERROR: {e}')
"
```

### Verify Database Tables
```bash
# Check if new tables exist (run as postgres user)
sudo -u postgres psql -d auditwise -c "\dt qaco.planning.*"
```

---

## **7. DEBUGGING & DIAGNOSTICS**

### Enable Odoo Debug Mode (Temporarily)
```bash
# Edit Odoo config file
sudo nano /etc/odoo/odoo.conf
# Add: log_level = debug

# Restart service
sudo systemctl restart odoo
```

### Check for Configuration Errors
```bash
# Validate Odoo config
sudo -u odoo odoo --config=/etc/odoo/odoo.conf --check-config
```

---

## **8. MONITORING & ALERTS SETUP**

### Log Monitoring
```bash
# Set up log rotation and monitoring
sudo logrotate -f /etc/logrotate.d/odoo

# Monitor for errors
grep -i "error\|exception" /var/log/odoo/odoo-server.log | tail -10
```

### Process Monitoring
```bash
# Ensure Odoo processes are running
ps aux | grep odoo

# Check memory usage
ps -o pid,ppid,cmd,%mem,%cpu --sort=-%mem | head
```

---

## **9. ROLLBACK PROCEDURES**

### If Deployment Fails
```bash
# Stop service
sudo systemctl stop odoo

# Rollback code
cd /var/odoo/auditwise.thinkoptimise.com/extra-addons/alamaudit
git reset --hard HEAD~1

# Restart service
sudo systemctl start odoo

# Monitor logs
sudo tail -f /var/log/odoo/odoo-server.log
```

### Emergency Database Backup
```bash
# Create backup before major changes
sudo -u postgres pg_dump auditwise > auditwise_backup_$(date +%Y%m%d_%H%M%S).sql
```

---

## **10. SUCCESS CRITERIA CHECKLIST**

- [ ] Odoo service starts without errors
- [ ] Web interface loads (HTTP 200)
- [ ] Planning Phase module loads successfully
- [ ] No NameError in logs
- [ ] Database connections established
- [ ] All P-tabs accessible in UI
- [ ] Cron jobs execute normally
- [ ] Memory/CPU usage within normal limits

---

## **CONTACT & ESCALATION**

If issues persist after following this guide:
1. Collect all log files: `/var/log/odoo/odoo-server.log`
2. Note exact error messages and timestamps
3. Check system resources during failure
4. Contact system administrator or Odoo support

**Estimated Resolution Time**: 15-30 minutes for successful deployment</content>
<parameter name="filePath">c:\Users\HP\Documents\GitHub\alamaudit\ODOO_DEPLOYMENT_TROUBLESHOOTING_GUIDE.md