import glob, re
from lxml import etree

errors = []
# collect known models from python files
known = set()
import ast
for f in glob.glob('**/models/*.py', recursive=True):
    text = open(f, encoding='utf-8').read()
    try:
        tree = ast.parse(text)
    except Exception:
        continue
    for c in [n for n in tree.body if isinstance(n, ast.ClassDef)]:
        model_name = None
        for node in c.body:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == '_name':
                        if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                            known.add(node.value.value)

CORE_PREFIXES = ('res','hr','account','ir','web','mail','base','uom','stock','product','sale','purchase','crm')
for xmlf in glob.glob('**/views/*.xml', recursive=True):
    try:
        tree = etree.parse(xmlf)
    except Exception:
        continue
    for view in tree.findall('.//record'):
        model_field = view.find("field[@name='model']")
        if model_field is None:
            continue
        model = (model_field.text or '').strip()
        # Ignore known core or external models that are not part of this repo
        if model and model not in known:
            if model.split('.')[0] in CORE_PREFIXES:
                # core/external model — skip as it's not expected in this repo
                continue
            errors.append((xmlf, model))

print('Views referencing unknown models:', len(errors))
for e in errors:
    print(e)