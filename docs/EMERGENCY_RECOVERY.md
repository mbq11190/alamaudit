# Emergency Recovery — Registry KeyError (e.g., KeyError: 'onboarding_id')

This guide explains safe, reversible steps to recover an Odoo 17 instance when the registry fails to load due to missing inverse field contracts.

## Symptoms
- Odoo fails to boot: `KeyError: 'onboarding_id'` in logs
- HTTP 500 on `/web`
- Cron jobs crash repeatedly

## Immediate containment (goal: bring Odoo back online)
1. **Identify the failing time window** from logs (journalctl or odoo logfile).
2. **Disable the offending module** (replace `<module>` and `<db>`):

   sudo ./scripts/containment_disable_module.sh <db> <module>

   This marks the module as `to remove` so the registry does not attempt to load it on startup.
3. **Restart Odoo** and verify registry loads: `sudo systemctl restart odoo` and `sudo journalctl -u odoo -f`.

## Diagnose offline (safe, non-invasive)
- Grep server log for `KeyError` and the file/module path that raises the exception.
- Use the generator script to propose a fix:

  python scripts/generate_inverse_fix.py --comodel '<comodel>' --inverse 'onboarding_id' --parent 'qaco.client.onboarding' --module '<module_name>'

## Fixing the code (ORM-correct)
- If the comodel truly lacks the Many2one, add a `fields.Many2one` to the comodel (preferred):

```py
onboarding_id = fields.Many2one(
    'qaco.client.onboarding',
    string='Onboarding',
    ondelete='cascade',
    index=True,
)
```

- If the inverse_name is wrong, correct the One2many inverse to the actual field on the comodel.

## Upgrade & Test
- After applying patch: `./odoo-bin -u <module> -d <db> --stop-after-init`
- Confirm logs show: `Registry loaded on db <db>`
- Restart Odoo and verify `/web` and `ir_cron` work

## Preventive
- Run `python scripts/validate_inverse_relations.py` in CI prior to deploy
- Use the `ci/inverse-validator` branch to gate PRs

If you need, I can prepare a PR that adds the actual fix (once you provide the traceback or the offending module/file).