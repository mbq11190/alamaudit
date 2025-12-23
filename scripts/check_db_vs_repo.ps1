param(
    [Parameter(Mandatory=$true)][string]$db,
    [string]$psql="psql",
    [string]$python="python",
    [string]$repo_models_file="repo_models.txt",
    [string]$db_models_file="db_models.txt"
)

# Generate repo model list
Write-Host "Generating repo model list..."
& $python scripts/compare_repo_models.py > $repo_models_file

# Dump DB model list
Write-Host "Dumping ir_model list from DB '$db'..."
$cmd = "$psql -d $db -c \"COPY (SELECT model FROM ir_model ORDER BY model) TO STDOUT;\" > $db_models_file"
Write-Host $cmd
Invoke-Expression $cmd

# Normalize files (remove empty lines)
$repo = Get-Content $repo_models_file | Where-Object { $_ -and $_.Trim().Length -gt 0 }
$dbm = Get-Content $db_models_file | Where-Object { $_ -and $_.Trim().Length -gt 0 }

# Compare
Write-Host "Models present in repo but missing in DB:" -ForegroundColor Yellow
$repo | Where-Object { $_ -notin $dbm } | Sort-Object | ForEach-Object { Write-Host $_ }

Write-Host "`nModels present in DB but missing in repo (possible orphans):" -ForegroundColor Yellow
$dbm | Where-Object { $_ -notin $repo } | Sort-Object | ForEach-Object { Write-Host $_ }

Write-Host "\nDone. Review the results and consider running scripts/orphan_ir_model_checks.sql on DB for further inspection." -ForegroundColor Green
