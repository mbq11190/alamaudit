import re
from pathlib import Path

view_path = Path('views/planning_phase_views.xml')
view_text = view_path.read_text(encoding='utf-8')
field_names = {m.group(1) for m in re.finditer(r'<field[^>]*name=["\'"\x02](\w+)["\'"\x02]', view_text)}

model_path = Path('models/planning_phase.py')
model_text = model_path.read_text(encoding='utf-8')
model_fields = {m.group(1) for m in re.finditer(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*fields\.', model_text)}

missing = sorted(f for f in field_names if f not in model_fields)
print('fields in view total', len(field_names))
print('fields defined', len(model_fields))
print('missing count', len(missing))
if missing:
    print('Missing fields referenced in view but not defined in model:')
    for f in missing:
        print(' ', f)
