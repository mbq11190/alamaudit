#!/usr/bin/env python3
"""Search repository for model definitions and check a list of model names.
Usage: python scripts/check_missing_models.py model.name1 model.name2 ...
Prints file paths that define the model or indicates not found.
"""
import sys
from pathlib import Path
import re

if len(sys.argv) < 2:
    print("Usage: check_missing_models.py model.name [model.name...]")
    sys.exit(2)

ROOT = Path(__file__).resolve().parents[1]
models_to_check = sys.argv[1:]
# Map model name -> list(files)
found = {m: [] for m in models_to_check}
name_re_template = lambda model: re.compile(r"_name\s*=\s*['\"]%s['\"]" % re.escape(model))

for p in ROOT.rglob('*.py'):
    try:
        text = p.read_text(encoding='utf-8')
    except Exception:
        continue
    for model in models_to_check:
        if name_re_template(model).search(text):
            found[model].append(str(p))

for model, files in found.items():
    if files:
        print(f"FOUND: {model}")
        for f in files:
            print("  ->", f)
    else:
        print(f"MISSING: {model} (no _name definition found in repository)")
