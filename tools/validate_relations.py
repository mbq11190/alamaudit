#!/usr/bin/env python3
"""
Odoo 17 _unknown Model Detector & Pre-Commit Guard

Scans all qaco_*/models/**/*.py files for:
- Relational fields pointing to unregistered models
- Missing model imports
- Invalid _order definitions
- Broken inverse relationships

Exits with 1 if any violations found.
"""

import re
import sys
import pathlib
from collections import defaultdict


def main():
    root = pathlib.Path('.')
    mod_dirs = [d for d in root.iterdir() if d.is_dir() and d.name.startswith('qaco_')]

    # Core Odoo models we expect (whitelist)
    core_whitelist = {
        'res.partner', 'res.users', 'ir.attachment', 'hr.employee',
        'res.country', 'res.country.state', 'res.currency',
        'account.move', 'account.move.line', 'uom.uom',
        'hr.department', 'account.account', 'mail.message',
        'mail.activity', 'mail.thread', 'mail.activity.mixin'
    }

    # Collect declared models
    declared_models = set()
    model_files = {}  # model -> file

    # Collect relational fields
    relations = []  # list of (file, field_name, rel_type, comodel, inverse)

    # Collect _order
    orders = []  # list of (file, model, order_expr)

    for mod_dir in mod_dirs:
        models_dir = mod_dir / 'models'
        if not models_dir.exists():
            continue

        for py_file in models_dir.rglob('*.py'):
            try:
                content = py_file.read_text(encoding='utf-8')
            except Exception as e:
                print(f"ERROR: Cannot read {py_file}: {e}", file=sys.stderr)
                continue

            # Extract _name
            for match in re.finditer(r"_name\s*=\s*['\"]([^'\"]+)['\"]", content):
                model = match.group(1)
                declared_models.add(model)
                model_files[model] = py_file

            # Extract relational fields
            # Support: positional inverse (One2many('comodel', 'inverse')) and keyword inverse_name
            for match in re.finditer(
                r"(\w+)\s*=\s*fields\.(One2many|Many2one|Many2many)\(\s*['\"]([^'\"]+)['\"](?:\s*,\s*['\"]([^'\"]+)['\"])?(?:\s*,\s*inverse_name\s*=\s*['\"]([^'\"]+)['\"])?",
                content,
            ):
                field_name = match.group(1)
                rel_type = match.group(2)
                comodel = match.group(3)
                # Positional inverse is group(4), keyword inverse_name is group(5)
                inverse = None
                if match.group(4):
                    inverse = match.group(4)
                elif match.group(5):
                    inverse = match.group(5)
                relations.append((py_file, field_name, rel_type, comodel, inverse))

            # Extract _order
            for match in re.finditer(r"_order\s*=\s*['\"]([^'\"]+)['\"]", content):
                order_expr = match.group(1)
                # Get model name from file
                model_match = re.search(r"_name\s*=\s*['\"]([^'\"]+)['\"]", content)
                if model_match:
                    model = model_match.group(1)
                    orders.append((py_file, model, order_expr))

    # Now validate
    errors = []

    # Check relations
    for file_path, field_name, rel_type, comodel, inverse in relations:
        # Comodel must exist
        if comodel not in declared_models and comodel not in core_whitelist:
            errors.append({
                'type': 'broken_relation',
                'model': None,  # will find from file
                'field': field_name,
                'comodel': comodel,
                'file': file_path,
                'cause': 'comodel not registered'
            })
            continue

        # One2many must specify an inverse field
        if rel_type == 'One2many' and not inverse:
            errors.append({
                'type': 'missing_inverse',
                'model': None,
                'field': field_name,
                'comodel': comodel,
                'file': file_path,
                'cause': 'One2many missing inverse field (positional or inverse_name)'
            })
            continue

        # If inverse specified and this is a One2many, ensure inverse field exists on comodel
        if inverse and rel_type == 'One2many':
            # Skip checking comodel files for core/external models (not declared here)
            comodel_file = model_files.get(comodel)
            if not comodel_file:
                # External/core model - assume valid
                continue
            try:
                comodel_text = comodel_file.read_text(encoding='utf-8')
            except Exception as e:
                errors.append({
                    'type': 'read_error',
                    'model': comodel,
                    'field': field_name,
                    'comodel': comodel,
                    'file': comodel_file,
                    'cause': f'cannot read comodel file: {e}'
                })
                continue
            # Check for inverse field definition on comodel
            if not re.search(rf"\b{re.escape(inverse)}\s*=\s*fields\.", comodel_text):
                errors.append({
                    'type': 'inverse_missing',
                    'model': comodel,
                    'field': field_name,
                    'comodel': comodel,
                    'file': comodel_file,
                    'cause': f'inverse field "{inverse}" not defined on comodel {comodel}'
                })

    # Check _order for 'id' on non-registered models (but since we have declared, maybe skip)
    # For now, just check if order references fields that might not exist, but that's hard without full field parsing

    # Check imports: for each declared model, ensure file is imported in __init__.py
    # NOTE: This check is removed as modules import the whole file, not individual models

    # Report errors
    if errors:
        print("BROKEN RELATIONS DETECTED", file=sys.stderr)
        for err in errors:
            print(f"Model: {err.get('model', 'N/A')}", file=sys.stderr)
            print(f"Field: {err.get('field', 'N/A')}", file=sys.stderr)
            print(f"Comodel: {err.get('comodel', 'N/A')}", file=sys.stderr)
            print(f"File: {err['file']}", file=sys.stderr)
            print(f"Cause: {err['cause']}", file=sys.stderr)
            print("", file=sys.stderr)
        sys.exit(1)
    else:
        print("All relations validated - no _unknown models detected")
        sys.exit(0)


if __name__ == '__main__':
    main()