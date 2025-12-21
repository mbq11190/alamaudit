import ast, glob, re

# Build model -> fields mapping
models = {}  # model_name -> set of field names
for f in glob.glob('**/models/*.py', recursive=True):
    text = open(f, encoding='utf-8').read()
    try:
        tree = ast.parse(text)
    except Exception:
        continue
    for c in [n for n in tree.body if isinstance(n, ast.ClassDef)]:
        model_name = None
        fields_set = set()
        for node in c.body:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == '_name':
                        if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                            model_name = node.value.value
                # field defs
                if isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Attribute):
                    if isinstance(node.value.func.value, ast.Name) and node.value.func.value.id == 'fields':
                        for target in node.targets:
                            if isinstance(target, ast.Name):
                                fields_set.add(target.id)
        if model_name:
            models[model_name] = fields_set

# Find related fields
problems = []
for f in glob.glob('**/models/*.py', recursive=True):
    text = open(f, encoding='utf-8').read()
    # find patterns like related='a.b' or related="a.b"
    for m in re.finditer(r"\b(\w+)\s*=\s*fields\.(?:Many2one|One2many|Many2many|Char|Text|Html|Float|Date|Datetime|Boolean)\([^\)]*related\s*=\s*['\"]([^'\"]+)['\"]", text, re.S):
        field_name = m.group(1)
        chain = m.group(2)
        # try to determine model where this field is defined
        # find enclosing class _name
        classblock = re.search(r"class\s+([A-Za-z0-9_]+)\s*\(.*?\):[\s\S]*?\b"+re.escape(field_name)+r"\s*=?\s*fields", text)
        model = None
        if classblock:
            # locate _name in class
            class_name = classblock.group(1)
            # find _name assignment in file for that class
            # crude search
            cn_re = re.compile(r"class\s+"+re.escape(class_name)+r"[\s\S]*?_name\s*=\s*['\"]([^'\"]+)['\"]")
            mcn = cn_re.search(text)
            if mcn:
                model = mcn.group(1)
        # If model not found, try to infer from filename
        if not model:
            # find model by checking file for any _name occurrence earlier
            pass
        # validate chain: each step should be a field on the previous model
        parts = chain.split('.')
        curr_model = model
        valid = True
        if curr_model is None:
            valid = False
        else:
            for part in parts:
                if curr_model not in models or part not in models[curr_model]:
                    valid = False
                    break
                # attempt to get next model by finding comodel name of that field
                # We don't have comodel mapping, so skip deeper validation
                # But we can at least assert the field exists
                # For deeper check, we'd need to parse field args, a heavier task
        if not valid:
            problems.append((f, model or 'unknown', field_name, chain))

print('Related chain issues found:', len(problems))
for p in problems:
    print(p)