# Copilot / Agent Instructions for alamaudit

## Architecture snapshot
- `qaco_audit` drives the audit lifecycle (stage gating, followers, smart buttons) and every phase module (`qaco_client_onboarding`, `qaco_planning_phase`, `qaco_execution_phase`, `qaco_finalisation_phase`, `qaco_deliverables`, `qaco_quality_review`) depends on it, shares the `audit_id`/`client_id` relationship, and most have `auto_install=True`.
- `qaco_employees` feeds HR records (partners, team leads, leave workflows); its README documents custom leave-adjustment behavior assumed by `qaco_audit` domain filters.
- Each module keeps to Odoo's MVC layout: `models/` for business logic, `views/` for XML forms/smart buttons, `data/` for seeds (stages, sequences, onboarding templates), `security/` for groups/access, and optional `migrations/<version>/` for structured schema moves.
- Helper utilities in `scripts/` validate the planning XML (`check_fields.py`, `check_fields_summary.py`, `check_planning_xml.py`, `run_check_planning_xml.bat`) without spinning up Odoo; run them when editing `qaco_planning_phase/views/planning_phase_views.xml`.

## Cross-module behaviors
- `qaco.audit` enforces access-heavy operations (`copy`, `unlink`, stage moves) and sequences audits via `ir.sequence`. Stage transitions call `_fields` metadata to build error messages; modifying this logic demands updates to `qaco_audit/tests/test_copy.py` or new TransactionCase tests.
- Smart buttons (see `qaco_planning_phase/views/audit_smart_button.xml`) open or lazily create related records via helpers like `action_open_client_onboarding`; reuse this pattern when another phase must be surfaced on the audit form.
- `qaco.client.onboarding` models ISA-aligned sections with traffic-light selections. `_populate_checklist_from_templates` and `_populate_preconditions` seed One2many rows on `create`, while constraints rely on regex checks (NTN/STRN) and cross-field guards; expect to maintain these helpers rather than sprinkling validation inline.
- `qaco.planning.phase` aggregates status, attachment, and checklist readiness into `can_finalize_planning`. Sign-off actions (`action_manager_sign`, `action_partner_sign`, `action_mark_planning_complete`) funnel through `_ensure_statuses_green`, `_validate_materiality_parameters`, and risk-register presence—use these helpers whenever introducing new completion gates.

## Data, configs, and automation hooks
- Manifests follow `version='17.0.x.y'`, declare XML in load order, and many set `auto_install=True` so they install right after `qaco_audit`. Whenever you add views/security/data, keep manifests synchronized or Odoo will ignore the file.
- `qaco_audit/hooks.py` houses a destructive `pre_init_hook` (renames `firm_name`, deletes `ir_model_fields` metadata), a `post_init_hook` that marks all phase modules for installation, and an `uninstall_hook` that removes them. Never execute installs/upgrades against production without a tested backup and a rollback plan.
- Seed records (audit stages, firm names, onboarding templates, planning smart buttons) are referenced via XML IDs (`env.ref('module.record_id')`). Renaming or deleting IDs breaks computed fields, smart buttons, and tests—migrate data instead of editing IDs in place.
- Use migrations under `migrations/<version>/` for structural DB changes; reserve hooks for one-off correction of legacy deployments.

## Development workflow & testing
- Run modules inside Odoo: `odoo-bin -i qaco_audit --test-enable -d <db> --stop-after-init` for clean installs, or `odoo-bin -u qaco_planning_phase -d <db>` for upgrades. Ensure this repository is on the `addons_path` so auto-install dependencies resolve.
- Existing automated coverage lives in `qaco_audit/tests/test_copy.py` (TransactionCase verifying the `copy` override resets partner fields). Model-level changes with business rules should extend this pattern, e.g., add cases for new stage guards.
- Logging is already wired in hooks and long-running computations; prefer `_logger` plus chatter (`message_post`) over ad-hoc prints so behavior stays observable in production.

## Coding conventions to mirror
- Inherit `mail.thread`/`mail.activity.mixin` for user-facing models and set `tracking=True` on significant fields so audit chatter remains consistent across modules.
- Attachment collections are explicit `Many2many('ir.attachment', '<rel>', 'phase_id', 'attachment_id')` tables with descriptive `help`; follow the current naming scheme when adding documentation buckets.
- Access relies on XML groups such as `qaco_audit.group_audit_partner`; adjust both `security/security_groups.xml` and `security/ir.model.access.csv` any time you touch permissions, and reference the IDs via `env.ref`.
- Guard actions should raise `UserError`/`ValidationError` with prescriptive copy (see planning-phase helpers and onboarding constraints) instead of silent failures. Centralize new guards in helper methods so they can be called from multiple actions.

## Preferences & reminders
- When proposing DB or seed-data changes, describe rollback/migration steps explicitly and state whether the change belongs in `migrations/` versus another hook.
- Repository preference: "Enable Claude Haiku 4.5 for all clients" (documented request; no code automation for this yet).
