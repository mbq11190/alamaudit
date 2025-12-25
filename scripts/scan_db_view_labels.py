"""Scan ir_ui_view.arch_db for <label> elements missing 'for' or 'class=\"o_form_label\"'.

Usage:
  python scripts/scan_db_view_labels.py --dsn "dbname=odoo user=odoo host=localhost"  # just report
  python scripts/scan_db_view_labels.py --dsn "..." --fix --confirm   # apply fixes (requires backup!)

This tool is conservative: it only adds class="o_form_label" to <label> tags
that have a string attribute but lack both for and o_form_label. When --fix
is used it will write the updated arch back to ir_ui_view (via SQL) after
creating a backup table.

Note: Requires psycopg2 to be installed in the environment where it's run.
"""
import argparse
import os
import sys
import re

try:
    import psycopg2
except Exception:
    psycopg2 = None

try:
    from lxml import etree
except Exception:
    etree = None

parser = argparse.ArgumentParser()
parser.add_argument("--dsn", help="libpq DSN string, e.g. 'dbname=odoo user=odoo host=localhost'")
parser.add_argument("--fix", action="store_true", help="Apply fixes to views (adds o_form_label where needed)")
parser.add_argument("--confirm", action="store_true", help="Confirm destructive operation --fix will not run without this flag")
args = parser.parse_args()

if psycopg2 is None:
    print("psycopg2 is not installed. Install it (pip install psycopg2-binary) to use this script.")
    sys.exit(1)

if not args.dsn:
    print("Provide a DSN using --dsn 'dbname=... user=... host=...'")
    sys.exit(1)

conn = psycopg2.connect(args.dsn)
conn.autocommit = False
cur = conn.cursor()

# Find candidate views containing <label tags
cur.execute("SELECT id, name, module, arch_db FROM ir_ui_view WHERE active = true AND arch_db ILIKE '%<label %'")
rows = cur.fetchall()
print(f"Found {len(rows)} active views that contain '<label' tokens")

offending = []
for vid, name, module, arch in rows:
    if not arch:
        continue
    try:
        if etree is not None:
            root = etree.fromstring(arch.encode("utf-8"))
            labels = root.xpath('.//label')
            for lbl in labels:
                has_string = 'string' in lbl.attrib
                has_for = 'for' in lbl.attrib
                has_class = 'class' in lbl.attrib and 'o_form_label' in lbl.attrib.get('class','')
                if has_string and not has_for and not has_class:
                    offending.append((vid, name, module, etree.tostring(lbl, encoding='unicode')))
        else:
            # Fallback: regex detect (less accurate but helpful)
            # Find <label .../> or <label ...></label>
            for m in re.finditer(r'<label\s+([^>]*?)(?:/?>)', arch, re.IGNORECASE | re.DOTALL):
                attrs = m.group(1)
                if 'string=' in attrs and 'for=' not in attrs and 'o_form_label' not in attrs:
                    offending.append((vid, name, module, '<label ' + attrs + '>'))
    except Exception as e:
        print(f"Skipping view {vid} due to parse error: {e}")

if not offending:
    print("No offending stored views detected.")
    conn.close()
    sys.exit(0)

print("Offending views:")
for vid, name, module, lbl in offending:
    print(f" - id={vid} module={module} name={name} label={lbl}")

if args.fix:
    if not args.confirm:
        print("Refusing to make DB changes without --confirm. Rerun with --confirm to apply fixes.")
        conn.close()
        sys.exit(2)
    # Back up rows into a table
    try:
        cur.execute("CREATE TABLE IF NOT EXISTS backup_problematic_ir_ui_view AS SELECT * FROM ir_ui_view WHERE false")
        cur.execute("INSERT INTO backup_problematic_ir_ui_view SELECT v.* FROM ir_ui_view v WHERE v.id IN %s", (tuple({v[0] for v in offending}),))
        print("Backed up offending views into backup_problematic_ir_ui_view")
    except Exception as e:
        print("Failed to back up views:", e)
        conn.rollback()
        conn.close()
        sys.exit(1)

    # Apply fixes
    for vid, name, module, arch in rows:
        try:
            if not arch:
                continue
            changed = False
            if etree is not None:
                root = etree.fromstring(arch.encode('utf-8'))
                labels = root.xpath('.//label')
                for lbl in labels:
                    has_string = 'string' in lbl.attrib
                    has_for = 'for' in lbl.attrib
                    has_class = 'class' in lbl.attrib and 'o_form_label' in lbl.attrib.get('class','')
                    if has_string and not has_for and not has_class:
                        existing = lbl.attrib.get('class','').strip()
                        if existing:
                            lbl.attrib['class'] = (existing + ' o_form_label').strip()
                        else:
                            lbl.attrib['class'] = 'o_form_label'
                        changed = True
                if changed:
                    new_arch = etree.tostring(root, encoding='unicode')
                    cur.execute('UPDATE ir_ui_view SET arch_db = %s WHERE id = %s', (new_arch, vid))
                    print(f"Fixed view id={vid} name={name} module={module}")
            else:
                # Regex fallback: add class to offending <label ...>
                new_arch = re.sub(r'(<label\s+)([^>]*?)(string=\"[\s\S]*?\")([^>]*?)(>)', lambda m: m.group(1) + m.group(2) + m.group(3) + m.group(4).replace(m.group(4), m.group(4) + ' class="o_form_label"') + m.group(5), arch, flags=re.IGNORECASE)
                if new_arch != arch:
                    cur.execute('UPDATE ir_ui_view SET arch_db = %s WHERE id = %s', (new_arch, vid))
                    print(f"Fixed view id={vid} name={name} module={module} (regex)")
        except Exception as e:
            print(f"Failed to fix view id={vid}: {e}")
            conn.rollback()
            conn.close()
            sys.exit(1)
    conn.commit()
    print("All fixes applied and committed.")
    conn.close()
    sys.exit(0)

conn.close()
sys.exit(0)
