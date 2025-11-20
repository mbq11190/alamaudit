import pathlib
from lxml import etree

errors = []
for path in pathlib.Path('.').rglob('*.xml'):
    try:
        doc = etree.parse(path)
        root = doc.getroot()
        if root.tag != 'odoo':
            raise ValueError(f"Unexpected root {root.tag}")
    except Exception as exc:
        errors.append((path, exc))

if errors:
    for path, exc in errors:
        print(path)
        print(exc)
else:
    print('no errors')
