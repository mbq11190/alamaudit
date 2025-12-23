import ast
import glob
import xml.etree.ElementTree as ET

# Parse python model files to build model -> field names mapping
models = {}  # model_name -> set(fields)
for f in glob.glob("**/models/*.py", recursive=True):
    text = open(f, encoding="utf-8").read()
    try:
        tree = ast.parse(text)
    except SyntaxError:
        continue
    class_defs = [n for n in tree.body if isinstance(n, ast.ClassDef)]
    for c in class_defs:
        model_name = None
        fields_set = set()
        for node in c.body:
            if isinstance(node, ast.Assign):
                # look for _name assignment
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == "_name":
                        if isinstance(node.value, ast.Constant) and isinstance(
                            node.value.value, str
                        ):
                            model_name = node.value.value
                # look for field definitions: fields.Some
                if isinstance(node.value, ast.Call) and isinstance(
                    node.value.func, ast.Attribute
                ):
                    if (
                        isinstance(node.value.func.value, ast.Name)
                        and node.value.func.value.id == "fields"
                    ):
                        for target in node.targets:
                            if isinstance(target, ast.Name):
                                fields_set.add(target.id)
        if model_name:
            models[model_name] = fields_set

# Now parse view XMLs and check fields
problems = []
for f in glob.glob("**/views/*.xml", recursive=True):
    try:
        tree = ET.parse(f)
    except ET.ParseError:
        continue
    root = tree.getroot()
    for record in root.findall(".//record"):
        model = record.get("model")
        if model != "ir.ui.view":
            continue
        arch_field = record.find("field[@name='arch']")
        if arch_field is None or arch_field.text is None:
            continue
        try:
            arch = ET.fromstring(arch_field.text)
        except ET.ParseError:
            # sometimes arch may contain templates with t-call etc; skip parse errors
            continue
        # determine the model for which the view applies from the record (not always present)
        # try to find the <form> or <tree> element with model attribute; in many cases the record name contains model info
        # Fallback: try to locate parent view usage; here we will only check field names against models we know
        for field_el in arch.findall(".//field"):
            fname = field_el.get("name")
            if not fname:
                continue
            # Attempt to guess comodel: if this field is declared on a local model we can find it
            # Check against all models: if there is exactly one model with this field it's likely intended; otherwise skip
            candidates = [m for m, fs in models.items() if fname in fs]
            if not candidates:
                # collect as potential problem
                problems.append((f, record.get("id"), fname))

print("View fields not matched to any model fields (possible issues):", len(problems))
for p in problems:
    print(p[0], p[1], p[2])
