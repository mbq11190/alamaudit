"""Validate that One2many('comodel', 'onboarding_id') has a corresponding
Many2one onboarding_id field on the comodel's model file.

Usage: python scripts/validate_onboarding_relations.py
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


many2one_re = re.compile(r"onboarding_id\s*=\s*fields\.Many2one\(", re.I)

issues = []

# Find One2many usages with inverse 'onboarding_id'
for path in ROOT.rglob("*.py"):
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        continue
    for m in one2many_re.finditer(text):
        comodel, inverse = m.group(1), m.group(2)
        if inverse != "onboarding_id":
            continue
        # Search for model file declaring _name = comodel
        model_files = []
        for f in ROOT.rglob("*.py"):
            try:
                ft = f.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            if name_re_template(comodel).search(ft):
                model_files.append(f)
        if not model_files:
            issues.append((path, comodel, "MISSING_MODEL"))
            continue
        # Check each model file for onboarding_id Many2one
        ok = False
        for mf in model_files:
            try:
                mtext = mf.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            if many2one_re.search(mtext):
                ok = True
                break
        if not ok:
            issues.append((path, comodel, "MISSING_FIELD", model_files))

# Print results
if not issues:
    print(
        'OK: All One2many(..., "onboarding_id") references correspond to models defining onboarding_id Many2one.'
    )
else:
    print("Found issues:")
    for it in issues:
        if it[2] == "MISSING_MODEL":
            print(
                f"- {it[0]} references comodel '{it[1]}' but no model with _name='{it[1]}' was found in repo"
            )
        else:
            files = ", ".join(str(x) for x in it[3])
            print(
                f"- {it[0]} references comodel '{it[1]}' but no 'onboarding_id = fields.Many2one' was found in: {files}"
            )


# Exit code
sys.exit(1 if issues else 0)
