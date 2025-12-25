#!/usr/bin/env bash
set -euo pipefail

LOG_DIR="${GITHUB_WORKSPACE:-.}/artifacts"
mkdir -p "$LOG_DIR"

MODULES="qaco_planning_phase,qaco_execution_phase,qaco_client_onboarding,qaco_employees,ai_audit_management,qaco_quality_review,qaco_finalisation_phase,qaco_deliverables"
DB_NAME="ci_odoo_db"
DB_HOST="127.0.0.1"
DB_PORT="5432"
DB_USER="postgres"
DB_PASS="postgres"

echo "Waiting for Postgres on ${DB_HOST}:${DB_PORT}..."
for i in {1..60}; do
  if pg_isready -h ${DB_HOST} -p ${DB_PORT} -U ${DB_USER} >/dev/null 2>&1; then
    echo "Postgres is ready"
    break
  fi
  echo "Postgres not ready yet ($i/60)..."
  sleep 2
done

echo "Starting Odoo container to run upgrade for modules: $MODULES"
# Use host network so container can reach Postgres on localhost from the service
# Mount the repo as extra-addons into /mnt/extra-addons
# Capture logs to file
docker pull odoo:17 || true

docker run --rm --network host -v "${GITHUB_WORKSPACE}:/mnt/extra-addons:ro" odoo:17 odoo \
  --db_host=${DB_HOST} --db_port=${DB_PORT} --db_user=${DB_USER} --db_password=${DB_PASS} \
  -d ${DB_NAME} -u "${MODULES}" --stop-after-init 2>&1 | tee "${LOG_DIR}/odoo-upgrade.log" || true

# Save psql table list (best-effort)
echo "Saving DB tables list"
psql "postgresql://${DB_USER}:${DB_PASS}@${DB_HOST}:${DB_PORT}/postgres" -c "\dt" > "${LOG_DIR}/tables.txt" || true

# Simple failure summary - grep for ERROR
grep -i "ERROR" "${LOG_DIR}/odoo-upgrade.log" > "${LOG_DIR}/errors.txt" || true

# Print a short summary
echo "Logs saved to ${LOG_DIR}"
if [ -s "${LOG_DIR}/errors.txt" ]; then
  echo "Errors found during upgrade (first 50 lines):"
  head -n 50 "${LOG_DIR}/errors.txt" || true
  exit 1
else
  echo "No ERROR lines found in the upgrade log."
fi
