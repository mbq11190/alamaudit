# Copilot / Agent Instructions for alamaudit

This repository contains multiple Odoo addon modules (prefix `qaco_`). The guidance below focuses on the repository structure, recurring patterns, and actionable instructions an AI coding agent needs to be productive.

## Quick Architecture (why it looks like this)
- **Odoo addons**: Each top-level folder like `qaco_audit`, `qaco_execution_phase`, `qaco_planning_phase` is an Odoo module (contains `__manifest__.py`).
- **Server-side MVC**: Business logic lives in `models/`, UI definitions in `views/`, seed data in `data/`, access rules in `security/`, and migrations in `migrations/`.
- **Inter-module dependencies**: Modules declare dependencies in `__manifest__.py` (`depends` list) and frequently reference records via XML IDs (e.g. `env.ref('qaco_audit.group_audit_partner')`).

## Critical files and examples
- `qaco_audit/__manifest__.py` — module metadata and listed `data` files. Use it to see what a module installs.
- `qaco_execution_phase/models/execution_phase.py` — example of model design: Many2one relations to `qaco.audit`, fields with `tracking=True`, compute methods (`@api.depends`) and action methods (`action_*`).
- `qaco_audit/hooks.py` — contains `pre_init_hook` that executes raw SQL and modifies the DB schema BEFORE module install. Be cautious when installing/updating this module on production DBs.
- `qaco_audit/tests/test_copy.py` — tests use Odoo's `odoo.tests.common.TransactionCase`. Tests create data via `env[...]` and use `with_user(...)` and `env.ref(...)` for group/record references.
- `security/ir.model.access.csv` and `security/security_groups.xml` — define access and groups; tests and code reference these by XML ID (e.g. `qaco_audit.group_audit_partner`).

## Development workflows (how to run & debug)
- Install / run modules inside an Odoo instance. Modules here are not standalone Python apps — they must be loaded by `odoo` / `odoo-bin`.
- Common test command (standard Odoo approach):
```
odoo-bin -i <module_name> --test-enable -d <TEST_DB_NAME> --stop-after-init
```
Replace `<module_name>` with `qaco_audit`, `qaco_execution_phase`, etc. Tests in `tests/` are Odoo unit tests (TransactionCase/HttpCase).
- For local development, start Odoo with this repository included in `addons_path` and use logging to debug server-side behavior.

## Conventions and patterns to follow (project-specific)
- Module naming: modules use `qaco_` prefix and manifest `version` uses `17.0.x.y` (Odoo 17 target). Follow the same naming/version pattern for new modules.
- Use `__manifest__.py` to declare `data` files (XML), security, and dependencies. New views/data must be added there.
- Persisted seed data and sequences are XML files under `data/` — changes to those files will affect DB state when the module is installed.
- Migrations: database migrations live in `migrations/<version>/` and should be used for structural DB migrations rather than `pre_init_hook` when possible; note `pre_init_hook` is used here for special-casing legacy data.
- Security: prefer XML group/record references (`env.ref('module.identifier')`) in tests and code, and update `security/ir.model.access.csv` when adding models.

## Safety notes (non-obvious risks)
- **pre_init_hook**: `qaco_audit` has a `pre_init_hook` that runs raw SQL and deletes metadata in `ir_model_fields`. Installing/updating this module on production DBs can be destructive. When automating installs, always run in a safe test DB first.
- **Data files order**: `data` listed in the manifest is applied in order; adding/removing files can change installed state. Keep manifest ordering consistent.

## Small coding examples (copyable patterns)
- Referencing a security group in tests:
```
partner_user = self.env['res.users'].create({
    'name': 'Partner',
    'login': 'partner@example.com',
    'groups_id': [(6, 0, [self.env.ref('qaco_audit.group_audit_partner').id])],
})
```
- Computed field pattern (from `execution_phase.py`):
```
@api.depends('budgeted_hours', 'actual_hours')
def _compute_hours_variance(self):
    for record in self:
        if record.budgeted_hours:
            record.hours_variance = record.actual_hours - record.budgeted_hours
```

## Where to look for changes
- Models: `*/models/*.py`
- Views: `*/views/*.xml` and `*/wizard/*.xml`
- Seed data & sequences: `*/data/*.xml`
- Security: `*/security/*.xml`, `*/security/ir.model.access.csv`
- Tests: `*/tests/*.py`

## Agent preferences / environment notes
- Preferred behavior: when proposing changes that modify DB schema or seed data, include a clear rollback plan and mention whether a migration should go into `migrations/` or `pre_init_hook`.
- Recommended test run example for a module: `odoo-bin -i qaco_audit --test-enable -d test_db --stop-after-init`.
- Agent preference (user request): "Enable Claude Haiku 4.5 for all clients" — if you want this recorded as a repo-level preference for AI agents, confirm and I will add a standard short line here. Note: I cannot enable external services/org-level features; this file only records the preference for agents working locally.

If anything here is unclear or you'd like more examples (e.g., coding style, commit messages, or CI hooks), tell me which area to expand and I'll iterate.
