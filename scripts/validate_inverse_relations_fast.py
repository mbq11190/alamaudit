"""Faster validator for One2many inverses (improved accuracy).
Scans code (excluding scripts/docs/diagnostics) and finds One2many('comodel', 'inverse') and
checks that some file defines `_name = 'comodel'` and within those files there is an assignment
for the inverse field (e.g., 'inverse = fields.Many2one(' or 'inverse =').
"""
import re
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]

one2many_pattern = re.compile(r"fields\.One2many\(\s*['\"]([^'\"]+)['\"]\s*,\s*['\"]([^'\"]+)['\"]", re.I)
name_pattern = re.compile(r"_name\s*=\s*['\"]([^'\"]+)['\"]")
inv_assign_template = lambda inv: re.compile(r"^\s*%s\s*=\s*(fields\.Many2one\(|)" % re.escape(inv), re.M)

# Collect files to scan
py_files = [p for p in ROOT.rglob('*.py') if not any(part in ("scripts", "docs", "diagnostics") for part in p.parts)]

# Build comodel map
comodel_files = {}
for p in py_files:
    try:
        txt = p.read_text(encoding='utf-8')
    except Exception:
        continue
    for m in name_pattern.finditer(txt):
        name = m.group(1)
        comodel_files.setdefault(name, []).append((p, txt))

issues = []
for p in py_files:
    try:
        txt = p.read_text(encoding='utf-8')
    except Exception:
        continue
    for m in one2many_pattern.finditer(txt):
        comodel, inverse = m.group(1), m.group(2)
        files = comodel_files.get(comodel)
        if not files:
            issues.append((str(p), comodel, inverse, 'MISSING_MODEL'))
            continue
        ok = False
        inv_re = inv_assign_template(inverse)
        for fp, ftxt in files:
            # Quick check: if inverse field found as name in file
            if inv_re.search(ftxt):
                ok = True
                break
            # Also check if Many2one to parent exists (e.g., onboarding_id = fields.Many2one('parent'))
            if re.search(r"^\s*%s\s*=\s*fields\.Many2one\(" % re.escape(inverse), ftxt, re.M):
                ok = True
                break
        if not ok:
            issues.append((str(p), comodel, inverse, 'MISSING_FIELD', [str(x[0]) for x in files]))

if not issues:
    print('OK: All One2many inverses in repository have matching fields on comodels.')
    sys.exit(0)

print('Found inverse mismatches:')
for it in issues:
    if it[3] == 'MISSING_MODEL':
        print(f"- {it[0]} -> comodel '{it[1]}' inverse '{it[2]}': NO model with _name='{it[1]}' found")
    else:
        print(f"- {it[0]} -> comodel '{it[1]}' inverse '{it[2]}' missing field in: {', '.join(it[4])}")

sys.exit(1)
