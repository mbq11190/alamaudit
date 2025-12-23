"""Faster validator for One2many inverses.
Uses simple grep-style scanning to find One2many(...) occurrences and checks comodel files
for an assignment to the inverse field name.

Reports mismatches quickly for large repos.
"""
import re
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]

one2many_pattern = re.compile(r"fields\.One2many\(\s*['\"]([^'\"]+)['\"]\s*,\s*['\"]([^'\"]+)['\"]", re.I)
name_pattern = re.compile(r"_name\s*=\s*['\"]([^'\"]+)['\"]")

# Find all files containing One2many
one2many_files = []
for p in ROOT.rglob('*.py'):
    try:
        txt = p.read_text(encoding='utf-8')
    except Exception:
        continue
    if 'One2many' in txt and 'fields.One2many' in txt:
        one2many_files.append((p, txt))

# Map comodel name -> list of files declaring it
comodel_files = {}
for p in ROOT.rglob('*.py'):
    try:
        txt = p.read_text(encoding='utf-8')
    except Exception:
        continue
    m = name_pattern.search(txt)
    if m:
        name = m.group(1)
        comodel_files.setdefault(name, []).append((p, txt))

issues = []
for p, txt in one2many_files:
    for m in one2many_pattern.finditer(txt):
        comodel, inverse = m.group(1), m.group(2)
        files = comodel_files.get(comodel)
        if not files:
            issues.append((str(p), comodel, inverse, 'MISSING_MODEL'))
            continue
        ok = False
        inv_assign_re = re.compile(r"^\s*%s\s*=\s*fields\.Many2one\(|^\s*%s\s*=\s*" % (re.escape(inverse), re.escape(inverse)), re.M)
        for fp, ftxt in files:
            if inv_assign_re.search(ftxt):
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
