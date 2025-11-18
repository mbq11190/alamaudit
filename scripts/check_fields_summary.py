import re
from pathlib import Path

view_path = Path('qaco_planning_phase/views/planning_phase_views.xml')
view_text = view_path.read_text()
field_names = {m.group(1) for m in re.finditer(r'name=["\'"\x02](\w+)["\'"\x02]', view_text)}

model_path = Path('qaco_planning_phase/models/planning_phase.py')
model_text = model_path.read_text()
model_fields = {m.group(1) for m in re.finditer(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*fields\.', model_text)}

missing = sorted(f for f in field_names if f not in model_fields)
print(f'fields in view total: {len(field_names)}')
print(f'fields defined in model: {len(model_fields)}')
print(f'missing count: {len(missing)}')
print('first few missing (if any):', missing[:20])
