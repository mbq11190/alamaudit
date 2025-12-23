import ast
import glob
import re

# Parse models and field definitions
ModelInfo = {}
for f in glob.glob("**/models/*.py", recursive=True):
    text = open(f, encoding="utf-8").read()
    try:
        tree = ast.parse(text)
    except Exception:
        continue
    for c in [n for n in tree.body if isinstance(n, ast.ClassDef)]:
        model_name = None
        fields = {}  # name -> dict(type, comodel)
        for node in c.body:
            if isinstance(node, ast.Assign):
                # find _name
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == "_name":
                        if isinstance(node.value, ast.Constant) and isinstance(
                            node.value.value, str
                        ):
                            model_name = node.value.value
                # field defs
                if isinstance(node.value, ast.Call) and isinstance(
                    node.value.func, ast.Attribute
                ):
                    if (
                        isinstance(node.value.func.value, ast.Name)
                        and node.value.func.value.id == "fields"
                    ):
                        for target in node.targets:
                            if isinstance(target, ast.Name):
                                fname = target.id
                                ftype = node.value.func.attr
                                # find first arg if it's a string -> comodel
                                comodel = None
                                if node.value.args:
                                    first = node.value.args[0]
                                    if isinstance(first, ast.Constant) and isinstance(
                                        first.value, str
                                    ):
                                        comodel = first.value
                                # also check keywords like comodel_name
                                for kw in node.value.keywords:
                                    if (
                                        kw.arg
                                        in ("comodel_name", "relation", "comodel")
                                        and isinstance(kw.value, ast.Constant)
                                        and isinstance(kw.value.value, str)
                                    ):
                                        comodel = kw.value.value
                                fields[fname] = {"type": ftype, "comodel": comodel}
        if model_name:
            ModelInfo[model_name] = {"fields": fields, "file": f}

# Now find related fields and validate first part's comodel
problems = []
for model, info in ModelInfo.items():
    fields = info["fields"]
    for fname, meta in fields.items():
        # We only inspect fields that have 'related' in their definition text. To find the related value, we re-open the file and search the assignment.
        fpath = info["file"]
        text = open(fpath, encoding="utf-8").read()
        # find the assignment text for this field
        m = re.search(
            r"\b" + re.escape(fname) + r"\s*=\s*fields\.[A-Za-z0-9_]+\([^\)]*\)",
            text,
            re.S,
        )
        if not m:
            continue
        assign_text = m.group(0)
        # extract related value if present
        rm = re.search(r"related\s*=\s*['\"]([^'\"]+)['\"]", assign_text)
        if not rm:
            continue
        related = rm.group(1)
        first = related.split(".")[0]
        # check that first exists on model
        if first not in fields:
            problems.append((model, fname, related, fpath, "first_field_missing"))
            continue
        first_meta = fields[first]
        comodel = first_meta.get("comodel")
        if not comodel:
            problems.append((model, fname, related, fpath, "first_field_no_comodel"))
            continue
        # check that comodel exists in ModelInfo
        if comodel not in ModelInfo:
            problems.append(
                (model, fname, related, fpath, f"comodel_missing:{comodel}")
            )

print("Related-field comodel validation problems:", len(problems))
for p in problems:
    print(p)
