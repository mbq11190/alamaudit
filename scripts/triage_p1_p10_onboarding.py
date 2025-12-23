"""Triage One2many inverses for Planning P1-P10 and onboarding module.
Reports missing comodel _name or missing inverse field definitions and suggests fixes.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET_FILES = list(ROOT.glob('qaco_planning_phase/models/planning_p*.py')) + list(ROOT.glob('qaco_client_onboarding/models/*.py'))
one2many_re = re.compile(r"fields\.One2many\(\s*['\"]([^'\"]+)['\"]\s*,\s*['\"]([^'\"]+)['\"]", re.I)
name_re = re.compile(r"_name\s*=\s*['\"]([^'\"]+)['\"]")
inv_assign_re_template = lambda inv: re.compile(r"^\s*%s\s*=\s*" % re.escape(inv), re.M)

issues = []
for f in TARGET_FILES:
    try:
        txt = f.read_text(encoding='utf-8')
    except Exception:
        continue
    for m in one2many_re.finditer(txt):
        comodel, inverse = m.group(1), m.group(2)
        # find files with that _name
        found_files = []
        for g in ROOT.rglob('*.py'):
            try:
                gtxt = g.read_text(encoding='utf-8')
            except Exception:
                continue
            if name_re.search(gtxt) and any(name_re.findall(gtxt)[i]==comodel for i in range(len(name_re.findall(gtxt)))):
                found_files.append((g, gtxt))
        if not found_files:
            issues.append((str(f), comodel, inverse, 'MISSING_COMODEL'))
            continue
        ok = False
        for g, gtxt in found_files:
            if inv_assign_re_template(inverse).search(gtxt) or re.search(r"%s\s*=\s*fields\.Many2one\(" % re.escape(inverse), gtxt):
                ok = True
                break
        if not ok:
            issues.append((str(f), comodel, inverse, 'MISSING_INVERSE_FIELD', [str(x[0]) for x in found_files]))

# print results
if not issues:
    print('No issues found in P1-P10 and onboarding modules')
else:
    print('Issues identified:')
    for it in issues:
        if it[3]=='MISSING_COMODEL':
            print(f"- {it[0]} -> comodel '{it[1]}' inverse '{it[2]}': comodel not found")
        else:
            print(f"- {it[0]} -> comodel '{it[1]}' inverse '{it[2]}': missing inverse field in files: {', '.join(it[4])}")

# Exit with non-zero when issues found
import sys
sys.exit(1 if issues else 0)
