import re, glob
models=set()
for f in glob.glob('**/models/*.py', recursive=True):
    s=open(f,encoding='utf-8').read()
    for m in re.findall(r"fields\.Many2one\('\s*([^']+?)\s*'", s):
        models.add(m)
    for m in re.findall(r"fields\.One2many\('\s*([^']+?)\s*'", s):
        models.add(m)
    for m in re.findall(r"fields\.Many2many\('\s*([^']+?)\s*'", s):
        models.add(m)

missing=[]
for name in sorted(models):
    occurrences=[]
    for f in glob.glob('**/models/*.py', recursive=True):
        text=open(f,encoding='utf-8').read()
        if re.search(r"fields\.(Many2one|One2many|Many2many)\('\s*"+re.escape(name)+r"\s*'", text):
            occurrences.append(f)
    if occurrences:
        print(name)
        for o in occurrences:
            print('  -', o)

print('\nNote: above are comodel names and where they are referenced.')
