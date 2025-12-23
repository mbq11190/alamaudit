#!/usr/bin/env python3
"""Check web asset references and JS module definitions.
- Scans all __manifest__.py files for 'assets' entries and lists referenced files.
- Checks that referenced files exist.
- Scans repo JS files for `odoo.define('module.name'...)` to discover defined modules.
- Scans JS files for `require('module.name')` to find required modules and reports missing module definitions.

Usage: python scripts/check_js_assets.py
"""
import ast
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
manifests = list(ROOT.rglob('__manifest__.py'))

defined_modules = set()
requires = set()
js_files = list(ROOT.rglob('*.js'))
for p in js_files:
    try:
        t = p.read_text(encoding='utf-8')
    except Exception:
        continue
    for m in re.findall(r"odoo\.define\(['\"]([^'\"]+)['\"]", t):
        defined_modules.add(m)
    for r in re.findall(r"require\(['\"]([^'\"]+)['\"]\)", t):
        requires.add(r)

# Collect assets from manifests
missing_files = []
assets_refs = {}
for m in manifests:
    try:
        # parse manifest file ast to find dict literal
        txt = m.read_text(encoding='utf-8')
        tree = ast.parse(txt)
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == '':
                        pass
        # crude parse: eval safe literal by extracting the top-level dict
        d = eval(compile(txt, str(m), 'eval')) if False else None
    except Exception:
        d = None
    # fallback: exec in empty namespace to get manifest dict
    try:
        ns = {}
        exec(txt, ns)
        manifest = ns
    except Exception:
        manifest = None
    if manifest and '__name__' in manifest:
        # when exec, manifest contains all names; the manifest dict is usually at top-level
        # try to find a dict object assigned in file
        found = None
        for v in manifest.values():
            if isinstance(v, dict) and 'name' in v:
                found = v
                break
        if not found:
            continue
        assets = found.get('assets') or {}
        if assets:
            assets_refs[str(m.parent.name)] = assets
            # iterate asset groups
            for grp, lst in assets.items():
                for ref in lst:
                    # normalize ref path
                    # skip non file refs (e.g., {something})
                    if isinstance(ref, str) and (ref.endswith('.js') or ref.endswith('.xml') or ref.endswith('.scss') or ref.endswith('.css')):
                        f = ROOT / ref.lstrip('/')
                        if not f.exists():
                            missing_files.append((str(m.parent.name), grp, ref))

# Find required modules not defined
missing_modules = sorted([r for r in requires if r not in defined_modules])

# Output results
out = {
    'defined_js_modules_count': len(defined_modules),
    'required_js_modules_count': len(requires),
    'missing_js_modules': missing_modules,
    'missing_asset_files': missing_files,
}
print(json.dumps(out, indent=2))
# Also print short human summary
print('\nSummary:')
print(f"Defined JS modules: {len(defined_modules)}")
print(f"Required JS modules: {len(requires)}")
if missing_modules:
    print('\nMissing JS module definitions (required but not defined):')
    for m in missing_modules:
        print(' -', m)
else:
    print('\nNo missing JS module definitions detected (by static scan).')

if missing_files:
    print('\nMissing asset files referenced in manifests:')
    for pkg, grp, ref in missing_files:
        print(f" - pkg={pkg} group={grp} ref={ref}")
else:
    print('\nNo missing asset files detected in manifests.')
