# ========================================================================
# KeyError Elimination Script - SIMPLIFIED VERSION
# ========================================================================
Write-Host "`n🔴 ELIMINATING KeyError: auditwise.thinkoptimise.com`n" -ForegroundColor Red

$repo = "C:\Users\HP\Documents\GitHub\alamaudit"

# Step 1: Stop Odoo
Write-Host "[1/6] Stopping Odoo processes..." -ForegroundColor Cyan
$procs = Get-Process | Where-Object {$_.ProcessName -like "*odoo*"}
if ($procs) {
    $procs | Stop-Process -Force
    Write-Host "  ✅ Stopped $($procs.Count) process(es)" -ForegroundColor Green
} else {
    Write-Host "  ✅ No Odoo processes running" -ForegroundColor Green
}

# Step 2: Clear cache
Write-Host "`n[2/6] Clearing Python cache..." -ForegroundColor Cyan
cd $repo
$cache = Get-ChildItem -Recurse -Filter "__pycache__" -ErrorAction SilentlyContinue
if ($cache) {
    $cache | Remove-Item -Recurse -Force
    Write-Host "  ✅ Removed $($cache.Count) cache dir(s)" -ForegroundColor Green
} else {
    Write-Host "  ✅ No cache to clear" -ForegroundColor Green
}

# Step 3: Verify no violations
Write-Host "`n[3/6] Verifying code quality..." -ForegroundColor Cyan
cd "$repo\qaco_planning_phase\models"
$bad = Select-String -Pattern "@api\.depends.*\.id" -Path "*.py" -ErrorAction SilentlyContinue
if ($bad) {
    Write-Host "  ❌ FAIL: Found violations!" -ForegroundColor Red
    exit 1
} else {
    Write-Host "  ✅ No api.depends violations" -ForegroundColor Green
}

# Step 4: Check helper methods
Write-Host "`n[4/6] Checking helper methods..." -ForegroundColor Cyan
$base = Get-Content "$repo\qaco_planning_phase\models\planning_base.py" -Raw
if ($base -match "_get_default_currency" -and $base -match "_get_default_user") {
    Write-Host "  ✅ Helper methods present" -ForegroundColor Green
} else {
    Write-Host "  ❌ FAIL: Missing helpers!" -ForegroundColor Red
    exit 1
}

# Step 5: Verify module structure
Write-Host "`n[5/6] Verifying module structure..." -ForegroundColor Cyan
if (Test-Path "$repo\qaco_planning_phase\__manifest__.py") {
    Write-Host "  ✅ Module found" -ForegroundColor Green
} else {
    Write-Host "  ❌ FAIL: Module missing!" -ForegroundColor Red
    exit 1
}

# Step 6: Summary
Write-Host "`n[6/6] Summary" -ForegroundColor Cyan
Write-Host "=" * 70
Write-Host "  ✅ Odoo stopped" -ForegroundColor Green
Write-Host "  ✅ Cache cleared" -ForegroundColor Green
Write-Host "  ✅ Code validated" -ForegroundColor Green
Write-Host "  ✅ Helpers verified" -ForegroundColor Green
Write-Host "  ✅ Module structure OK" -ForegroundColor Green
Write-Host "=" * 70
Write-Host "`n✅ ALL CHECKS PASSED - Ready for module upgrade!" -ForegroundColor Green

# Next steps
Write-Host "`n📋 NEXT STEPS:`n" -ForegroundColor Cyan
Write-Host "1. Backup database:" -ForegroundColor Yellow
Write-Host "   pg_dump -U odoo -Fc auditwise.thinkoptimise.com > backup.dump`n"
Write-Host "2. Upgrade module:" -ForegroundColor Yellow
Write-Host "   cd C:\Program Files\Odoo 17\server"
Write-Host "   .\odoo-bin -c odoo.conf -u qaco_planning_phase -d auditwise.thinkoptimise.com --stop-after-init`n"
Write-Host "3. Start Odoo:" -ForegroundColor Yellow
Write-Host "   .\odoo-bin -c odoo.conf`n"
Write-Host "4. Monitor for errors:" -ForegroundColor Yellow
Write-Host "   Get-Content odoo.log -Wait`n"

Write-Host "🎯 Expected: Zero KeyError messages!" -ForegroundColor Green
