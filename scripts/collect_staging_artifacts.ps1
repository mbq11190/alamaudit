<#
PowerShell helper to run the safe orchestrator (if available) and collect key artifact files.
Usage: .\scripts\collect_staging_artifacts.ps1 -Db <dbname>
#>
param(
    [Parameter(Mandatory=$true)][string]$Db,
    [string]$SafeScript="./scripts/safe_odoo_fix.sh"
)

Write-Host "Running safe orchestrator for DB: $Db"
if (Test-Path $SafeScript) {
    if ($IsWindows) {
        Write-Host "Attempting to run via WSL..."
        wsl bash -lc "$SafeScript --db $Db"
    } else {
        bash -lc "$SafeScript --db $Db"
    }
} else {
    Write-Host "safe_orchestrator not found at $SafeScript; please run it manually on the staging host." -ForegroundColor Yellow
}

Write-Host "Look for artifacts in: ./scripts/"
Get-ChildItem -Path ./scripts -Filter 'first_traceback.txt*','db_models.txt*','orphan_report.txt*' -ErrorAction SilentlyContinue | ForEach-Object { Write-Host $_.FullName }

Write-Host "If you cannot run the orchestrator, run these (psql example):"
Write-Host "sudo -u postgres psql -d $Db -c \"COPY (SELECT model FROM ir_model ORDER BY model) TO STDOUT;\" > scripts/db_models.txt"
Write-Host "python scripts/find_first_traceback.py /path/to/upgrade-$Db.log > scripts/first_traceback.txt"
Write-Host "sudo -u postgres psql -d $Db -f scripts/orphan_ir_model_checks.sql > scripts/orphan_report.txt"
Write-Host "When done, paste the contents of the three files here in the chat." -ForegroundColor Green
