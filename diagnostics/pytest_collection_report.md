# Pytest Collection Diagnostic Report

**Date:** 2025-12-23
**Branch:** `ci/diagnostic-tests`

## Summary
Running `pytest -q` in the repository failed during test collection with 33 errors. All errors are ImportError / ModuleNotFoundError caused by a missing `odoo` package. This means the project tests require a running Odoo environment (and related test infrastructure) to import modules and collect tests.

## Key output (excerpt)
- Error: `ModuleNotFoundError: No module named 'odoo'`
- 33 errors during collection (examples include `ai_audit_management`, `qaco_audit`, `qaco_client_onboarding`, `qaco_employees`, `web_responsive` tests)

Full pytest collection output is recorded in the CI job logs and the local run that produced this report.

## Reproduction Steps (local)
1. Activate virtualenv used by repo:
   ```bash
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   ```
2. Run tests:
   ```bash
   python -m pytest -q
   ```
3. Observation: tests fail at collection with `ModuleNotFoundError: No module named 'odoo'`.

## Root cause
- Tests import Odoo modules and expect the `odoo` package to be available (and an Odoo runtime / database to be accessible for TransactionCase tests).
- CI environment currently does not provide an Odoo runtime nor `odoo` import, so collection fails immediately.

## Recommendations
1. Short term (diagnostic PR): keep the test job as **best-effort** but ensure collection errors don't block PRs, or gate the tests on presence of Odoo credentials or a Docker/service.
2. Medium term (recommended): Add a dedicated CI job that runs Odoo-backed tests inside a containerized Odoo environment:
   - Use a container image that provides Odoo + PostgreSQL and mounts repo as `addons_path`.
   - Start Odoo with `--dev=reload --test-enable` and run `odoo-bin -c <conf> -d <testdb> --i18n` or use the `odoo/test` images.
   - Use `odoo-bin -i <module>` with `--stop-after-init` to run module tests.
3. Alternative for pure unit tests: mark Odoo-dependent tests with a marker (e.g., `@pytest.mark.odoo`) and skip them in standard CI unless a `RUN_ODOO_TESTS=true` flag is set.
4. Add explicit instructions in `CONTRIBUTING.md` on how to run tests (requires Odoo, DB, and test fixtures).

## Next steps I can take (pick one)
- Create a CI job that spins up Odoo & Postgres in Docker and runs module tests (higher effort). ✅
- Add pytest markers to skip Odoo-dependent tests by default and add an Opt-in CI job to run them. ✅
- Add this diagnostic file to a branch and open a PR for review (this branch contains this diagnostic). ✅

---

If you'd like I can proceed to implement one of the recommended actions. If you want the full pytest output attached to this PR, I can add a raw log file as well. Let me know which path to take next.