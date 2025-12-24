#!/usr/bin/env python3
"""Static scan: find relational fields referencing comodels that have no _name="..." defined in repository.
Useful to catch typos / missing imports that lead to _unknown at runtime.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MODEL_FILES = list((ROOT / "qaco_client_onboarding" / "models").rglob("*.py")) + list((ROOT / "qaco_planning_phase" / "models").rglob("*.py")) + list((ROOT / "qaco_audit" / "models").rglob("*.py"))

re_model_name = re.compile(r"_name\s*=\s*['\"]([^'\"]+)['\"]")
re_rel_field = re.compile(r"fields\.(?:Many2one|One2many|Many2many)\(\s*['\"]([^'\"]+)['\"]")

defined_models = set()
used_comodels = set()

for f in MODEL_FILES:
    txt = f.read_text(encoding="utf-8")
    for m in re_model_name.findall(txt):
        defined_models.add(m)
    for m in re_rel_field.findall(txt):
        used_comodels.add(m)

missing = sorted(m for m in used_comodels if m not in defined_models)
if missing:
    print("Missing comodel definitions (referenced but no _name found):")
    for m in missing:
        print(" - ", m)
    sys.exit(2)
else:
    print("No missing comodels found in scanned modules.")
    sys.exit(0)
