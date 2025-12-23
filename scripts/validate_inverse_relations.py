"""Validate One2many inverse fields point to existing Many2one fields on comodels.

Scans Python files for `fields.One2many('comodel', 'inverse_name', ...)` and verifies
that at least one model file declares `_name = 'comodel'` and contains a definition for
`inverse_name = fields.Many2one(...)` (or any assignment to that name).

Exit code 0 on success, 1 when mismatches found.
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

one2many_re = re.compile(
    r"fields\.One2many\(\s*['\"]([^'\"]+)['\"]\s*,\s*['\"]([^'\"]+)['\"]", re.I
)
def name_re_template(model):
    return re.compile(r"_name\s*=\s*['\"]%s['\"]" % re.escape(model))


def field_assign_re(field):
    return re.compile(r"^\s*%s\s*=\s*" % re.escape(field), re.M)

issues = []

print("Scanning repository for One2many inverse references...")
for path in ROOT.rglob("*.py"):
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        continue
    for m in one2many_re.finditer(text):
        comodel, inverse = m.group(1), m.group(2)
        # find model files defining _name = comodel
        model_files = []
        for mf in ROOT.rglob("*.py"):
            try:
                mtext = mf.read_text(encoding="utf-8")
            except Exception:
                continue
            if name_re_template(comodel).search(mtext):
                model_files.append(mf)
        if not model_files:
            issues.append((str(path), comodel, inverse, "MISSING_MODEL"))
            continue
        ok = False
        for mf in model_files:
            try:
                mtext = mf.read_text(encoding="utf-8")
            except Exception:
                continue
            if field_assign_re(inverse).search(mtext):
                ok = True
                break
        if not ok:
            issues.append(
                (
                    str(path),
                    comodel,
                    inverse,
                    "MISSING_FIELD",
                    [str(x) for x in model_files],
                )
            )

if not issues:
    print("OK: All One2many inverse fields reference existing fields on comodels.")
    sys.exit(0)

print("\nFound inverse mismatches:\n")
for it in issues:
    if it[3] == "MISSING_MODEL":
        print(
            f"- {it[0]} -> comodel '{it[1]}' (inverse '{it[2]}'): NO model with _name='{it[1]}' found"
        )
    else:
        models = ", ".join(it[4])
        print(
            f"- {it[0]} -> comodel '{it[1]}' (inverse '{it[2]}'): Missing field on model files: {models}"
        )

sys.exit(1)
