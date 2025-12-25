import glob
import xml.etree.ElementTree as ET

import sys
problems = []
files = glob.glob("**/views/*.xml", recursive=True)
for f in files:
    try:
        tree = ET.parse(f)
    except Exception:
        continue
    root = tree.getroot()
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
                problems.append(
                    (f, record.get("id"), ET.tostring(label, encoding="unicode"))
                )

print("Problems found:", len(problems))
for p in problems:
    print(p[0], p[1], p[2])

# Exit non-zero if any problems found so CI fails fast
if problems:
    sys.exit(1)
