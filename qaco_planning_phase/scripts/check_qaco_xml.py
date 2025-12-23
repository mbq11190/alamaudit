import pathlib
import xml.etree.ElementTree as ET

root = pathlib.Path(__file__).resolve().parents[1]
modules = sorted([p for p in root.glob("qaco_*") if p.is_dir()])
files = []
for mod in modules:
    files.extend(sorted(mod.rglob("*.xml")))

problems = []
for f in files:
    try:
        tree = ET.parse(f)
    except ET.ParseError as e:
        problems.append((f, "parse_error", str(e)))
        continue
    root_elem = tree.getroot()
    if root_elem.tag != "odoo":
        problems.append((f, "root_not_odoo", root_elem.tag))
        continue
    other_children = [c.tag for c in root_elem if c.tag != "data"]
    if other_children:
        problems.append((f, "other_children", other_children))

print("Modules scanned:", len(modules))
print("XML files checked:", len(files))
if problems:
    print("Problems detected:")
    for path, kind, detail in problems:
        print(path, kind, detail)
else:
    print("No issues found.")
