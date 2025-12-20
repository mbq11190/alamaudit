import re
from pathlib import Path
from collections import defaultdict

views_path = Path(r'c:\Users\HP\Documents\GitHub\alamaudit\qaco_planning_phase\views')
xml_files = list(views_path.glob('*.xml'))

# Exclude .bak files
xml_files = [f for f in xml_files if not f.name.endswith('.bak')]

id_locations = defaultdict(list)
prefix_issues = []

pattern = re.compile(r'<record\s+id="([^"]+)"')

for xml_file in xml_files:
    try:
        with open(xml_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                match = pattern.search(line)
                if match:
                    xml_id = match.group(1)
                    id_locations[xml_id].append((xml_file.name, line_num))
                    
                    # Check for proper prefixing
                    valid_prefixes = ['view_', 'action_', 'menu_', 'model_']
                    if not any(xml_id.startswith(p) for p in valid_prefixes):
                        prefix_issues.append((xml_id, xml_file.name, line_num))
    except Exception as e:
        print(f'Error reading {xml_file.name}: {e}')

# Find duplicates
duplicates = {k: v for k, v in id_locations.items() if len(v) > 1}

print('=' * 80)
print('XML ID DUPLICATE CHECK REPORT')
print('=' * 80)
print()
print(f'Total XML files scanned: {len(xml_files)}')
print(f'Total unique XML IDs: {len(id_locations)}')
print(f'Total XML ID occurrences: {sum(len(v) for v in id_locations.values())}')
print()

if duplicates:
    print('🚨 DUPLICATE XML IDs FOUND:')
    print('=' * 80)
    for xml_id, locations in sorted(duplicates.items()):
        print(f'\n  ❌ {xml_id}')
        for file_name, line_num in locations:
            print(f'     - {file_name} (line {line_num})')
else:
    print('✅ ZERO duplicate XML IDs found - all IDs are unique')

print()
print('=' * 80)
print('PREFIX CONVENTION CHECK')
print('=' * 80)
print()
if prefix_issues:
    print(f'⚠️  {len(prefix_issues)} IDs without standard prefixes:')
    print('   (Expected: view_, action_, menu_, or model_)')
    print()
    for xml_id, file_name, line_num in prefix_issues[:20]:  # Show first 20
        print(f'  - {xml_id} in {file_name} (line {line_num})')
    if len(prefix_issues) > 20:
        print(f'  ... and {len(prefix_issues) - 20} more')
else:
    print('✅ All IDs follow standard prefix conventions')

print()
print('=' * 80)
