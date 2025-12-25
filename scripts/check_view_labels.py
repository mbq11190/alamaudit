import argparse
import glob
import xml.etree.ElementTree as ET
import io
import sys

parser = argparse.ArgumentParser(description="Check that <label> tags are valid for Odoo 17 views")
parser.add_argument("--autofix", action="store_true", help="Automatically add class=\"o_form_label\" to section labels")
args = parser.parse_args()

problems = []
changed_files = set()
# Scan all XML files in the repository (views can appear outside a views/ folder)
files = glob.glob("**/*.xml", recursive=True)
for f in files:
    try:
        tree = ET.parse(f)
    except Exception:
        # Skip any files that are not valid XML
        continue
    root = tree.getroot()
    modified = False
    for record in root.findall(".//record"):
        if record.get("model") != "ir.ui.view":
            continue
        arch = record.find('field[@name="arch"]')
        if arch is None:
            continue
        for label in arch.findall(".//label"):
            has_for = "for" in label.attrib
            has_class = "class" in label.attrib and "o_form_label" in label.attrib.get(
                "class", ""
            )
            if not has_for and not has_class:
                problems.append((f, record.get("id"), ET.tostring(label, encoding="unicode")))
                if args.autofix:
                    # Add the o_form_label class safely
                    existing = label.attrib.get("class", "").strip()
                    if existing:
                        label.set("class", existing + " o_form_label")
                    else:
                        label.set("class", "o_form_label")
                    modified = True
    if modified:
        # Write back the updated XML while preserving the file's encoding
        buf = io.BytesIO()
        tree.write(buf, encoding="utf-8", xml_declaration=True)
        with open(f, "wb") as fh:
            fh.write(buf.getvalue())
        changed_files.add(f)

print("Problems found:", len(problems))
for p in problems:
    print(p[0], p[1], p[2])

if args.autofix and changed_files:
    print("Auto-fixed files:")
    for cf in sorted(changed_files):
        print(" -", cf)

# Exit non-zero if any problems found and we didn't autofix them
if problems and not args.autofix:
    sys.exit(1)
