#!/usr/bin/env python3
"""Collect models declared in code and print them, to be compared with DB ir_model.
Usage: python scripts/compare_repo_models.py > repo_models.txt
Then run on DB: SELECT model FROM ir_model ORDER BY model; and diff lists.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
name_re = re.compile(r"^\s*_name\s*=\s*['\"]([^'\"]+)['\"]", re.M)
models = set()

for p in ROOT.rglob('*.py'):
    try:
        t = p.read_text(encoding='utf-8')
    except Exception:
        continue
    for m in name_re.findall(t):
        models.add(m)

for m in sorted(models):
    print(m)
