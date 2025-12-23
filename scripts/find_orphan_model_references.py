#!/usr/bin/env python3
"""Scan XML and CSV files for model references and find those not defined in repo models.
Outputs:
 - scripts/orphan_model_references.txt: list of model names referenced but not found in repo
 - scripts/suggested_model_stubs.py: Python file that contains minimal Odoo model class stubs for missing models (commented)
 - scripts/orphan_model_report.txt: human-readable report with locations and suggestions
"""
from pathlib import Path
import re
import csv

ROOT = Path(__file__).resolve().parents[1]
repo_models = set()
# reuse compare_repo_models logic
for p in ROOT.rglob('*.py'):
    try:
        t = p.read_text(encoding='utf-8')
    except Exception:
        continue
    for m in re.findall(r"^\s*_name\s*=\s*['\"]([^'\"]+)['\"]", t, re.M):
        repo_models.add(m)

# collect models referenced in XML and CSV
xml_model_refs = {}
for p in ROOT.rglob('*.xml'):
    try:
        t = p.read_text(encoding='utf-8')
    except Exception:
        continue
    for m in re.findall(r"model\s*=\s*\"([^\"]+)\"", t):
        xml_model_refs.setdefault(m, []).append(str(p))
    for m in re.findall(r"model\s*=\s*'([^']+)'", t):
        xml_model_refs.setdefault(m, []).append(str(p))

# collect models referenced in ir.model.access CSVs (parse properly: model_id is 3rd column)
csv_model_refs = {}
for p in ROOT.rglob('ir.model.access*.csv'):
    try:
        with p.open(encoding='utf-8') as fh:
            reader = csv.reader(fh)
            for parts in reader:
                if not parts:
                    continue
                # normalize length
                if len(parts) >= 3:
                    model_token = parts[2].strip()
                    csv_model_refs.setdefault(model_token, []).append(str(p))
    except Exception:
        continue

# Build mapping from xml model record ids like model_qaco_xyz -> actual model name if present in data XML
xml_model_id_map = {}
for p in ROOT.rglob('*.xml'):
    try:
        t = p.read_text(encoding='utf-8')
    except Exception:
        continue
    # find records of model ir.model
    for rec in re.findall(r"<record[^>]*id=\"([^\"]+)\"[^>]*model=\"ir.model\"[^>]*>(.*?)</record>", t, re.S):
        xml_id, inner = rec
        # find field name="model" value
        m = re.search(r"<field[^>]*name=\"model\"[^>]*>([^<]+)</field>", inner)
        if m:
            model_name = m.group(1).strip()
            xml_model_id_map[xml_id] = model_name
    # also with single quotes
    for rec in re.findall(r"<record[^>]*id='([^']+)'[^>]*model='ir.model'[^>]*>(.*?)</record>", t, re.S):
        xml_id, inner = rec
        m = re.search(r"<field[^>]*name='model'[^>]*>([^<]+)</field>", inner)
        if m:
            model_name = m.group(1).strip()
            xml_model_id_map[xml_id] = model_name

# Function to normalize a model token (like model_qaco_onboarding -> qaco.onboarding)
def normalize_model_token(token):
    if not token:
        return token
    token = token.strip()
    # if token already dotted name
    if '.' in token:
        return token
    # if token starts with model_ and we have mapping
    if token.startswith('model_'):
        if token in xml_model_id_map:
            return xml_model_id_map[token]
        # heuristic: remove prefix and replace _ with .
        return token[len('model_'):].replace('_', '.')
    return token

# Normalize csv_model_refs keys
normalized_csv_refs = {}
for k, v in csv_model_refs.items():
    nk = normalize_model_token(k)
    normalized_csv_refs.setdefault(nk, []).extend(v)

# combine refs
all_refs = set(xml_model_refs.keys()) | set(normalized_csv_refs.keys())

# Filter out obvious Odoo core models and non-model names
CORE_PREFIXES = ('ir.', 'res.', 'web.', 'mail.', 'hr.', 'auth_ldap', 'calendar.', 'account.', 'product.', 'stock.', 'sale.', 'purchase.', 'crm.', 'portal.', 'website.')
filtered_refs = set()
for r in all_refs:
    if not r:
        continue
    if r.startswith(CORE_PREFIXES):
        continue
    filtered_refs.add(r)

missing = sorted([m for m in filtered_refs if m not in repo_models])

# combine refs
all_refs = set(xml_model_refs.keys()) | set(csv_model_refs.keys())
missing = sorted([m for m in all_refs if m and m not in repo_models])

out_report = ROOT / 'scripts' / 'orphan_model_report.txt'
with out_report.open('w', encoding='utf-8') as f:
    f.write('Orphan Model References Report\n')
    f.write('=================================\n\n')
    f.write(f'Total repo models discovered: {len(repo_models)}\n')
    f.write(f'Total referenced models found in XML/CSV: {len(all_refs)}\n')
    f.write(f'Total missing (referenced but not defined in code): {len(missing)}\n\n')
    for m in missing:
        f.write(f'MISSING MODEL: {m}\n')
        if m in xml_model_refs:
            f.write('  Referenced in XML files:\n')
            for ln in xml_model_refs[m][:20]:
                f.write(f'    - {ln}\n')
        if m in csv_model_refs:
            f.write('  Referenced in CSV files:\n')
            for ln in csv_model_refs[m][:20]:
                f.write(f'    - {ln}\n')
        f.write('\n')

# write list file
list_path = ROOT / 'scripts' / 'orphan_model_references.txt'
list_path.write_text('\n'.join(missing), encoding='utf-8')

# generate suggested stub file
stub_path = ROOT / 'scripts' / 'suggested_model_stubs.py'
with stub_path.open('w', encoding='utf-8') as f:
    f.write('# Suggested Odoo model stubs for missing models\n')
    f.write('# Review and customize before enabling in a module package\n\n')
    for m in missing:
        cls = m.replace('.', '_')
        f.write(f"# class {cls}(models.Model):\n")
        f.write(f"#     _name = '{m}'\n")
        f.write("#     _description = 'AUTO-GENERATED STUB - REVIEW'\n")
        f.write("#     # TODO: add fields and business logic\n\n")

print('Orphan model scan complete')
print(f'Report: {out_report}')
print(f'List: {list_path}')
print(f'Suggested stubs: {stub_path}')
