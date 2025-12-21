#!/usr/bin/env python3
import re
from pathlib import Path
from collections import defaultdict

# Parse all related fields
related_fields = {}  # model.field -> related_path
many2one_fields = {}  # model.field -> target_model

for py_file in Path("qaco_planning_phase/models").rglob("*.py"):
    if "__pycache__" in str(py_file):
        continue
    
    content = py_file.read_text()
    model_match = re.search(r"_name\s*=\s*['\"]([^'\"]+)['\"]", content)
    if not model_match:
        continue
    model = model_match.group(1)
    
    # Find related fields
    for match in re.finditer(r"(\w+)\s*=\s*fields\.\w+\([^)]*related\s*=\s*['\"]([^'\"]+)['\"]", content):
        field = match.group(1)
        related = match.group(2)
        related_fields[f"{model}.{field}"] = related
    
    # Find Many2one fields
    for match in re.finditer(r"(\w+)\s*=\s*fields\.Many2one\(\s*['\"]([^'\"]+)['\"]", content):
        field = match.group(1)
        target = match.group(2)
        many2one_fields[f"{model}.{field}"] = target

print("SEARCHING FOR CIRCULAR RELATED FIELD CHAINS...\n")

# For each related field, trace the chain
for model_field, related_path in sorted(related_fields.items()):
    model = model_field.split('.')[0]
    chain = [model_field]
    current = related_path
    
    for _ in range(10):  # Max depth
        parts = current.split('.')
        if len(parts) < 2:
            break
        
        # First part is a field in current model
        first_field = parts[0]
        rest = '.'.join(parts[1:])
        
        # Find what model this field points to
        lookup_key = f"{model}.{first_field}"
        
        if lookup_key in related_fields:
            # This field is ALSO a related field - follow the chain
            chain.append(f"{lookup_key} (related={related_fields[lookup_key]})")
            current = related_fields[lookup_key]
        elif lookup_key in many2one_fields:
            # This is a Many2one - get target model
            target_model = many2one_fields[lookup_key]
            chain.append(f"{lookup_key} -> {target_model}")
            
            # Now check if target_model has the rest of the path as a related field
            next_field = f"{target_model}.{rest}"
            if next_field in related_fields:
                chain.append(f"{next_field} (related={related_fields[next_field]})")
                current = related_fields[next_field]
                model = target_model
            else:
                break
        else:
            break
    
    if len(chain) > 3:  # Only show long chains
        print(f"\n{'='*80}")
        print(f"CHAIN for {model_field}:")
        for i, item in enumerate(chain):
            print(f"  {i+1}. {item}")

