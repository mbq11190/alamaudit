#!/usr/bin/env python3
"""Find circular related field chains that cause RecursionError during Odoo field setup."""

import re
from pathlib import Path
from collections import defaultdict

def parse_related_fields(module_path):
    """Parse all related fields from Python files in a module."""
    fields = []
    
    for py_file in Path(module_path).rglob("*.py"):
        if "__pycache__" in str(py_file):
            continue
            
        content = py_file.read_text()
        
        # Find model _name
        model_match = re.search(r"_name\s*=\s*['\"]([^'\"]+)['\"]", content)
        if not model_match:
            continue
        model_name = model_match.group(1)
        
        # Find all related fields
        for match in re.finditer(
            r"(\w+)\s*=\s*fields\.\w+\([^)]*related\s*=\s*['\"]([^'\"]+)['\"]",
            content
        ):
            field_name = match.group(1)
            related_path = match.group(2)
            
            fields.append({
                'file': py_file.name,
                'model': model_name,
                'field': field_name,
                'related': related_path
            })
    
    return fields

def build_dependency_graph(fields):
    """Build a graph of model dependencies through related fields."""
    graph = defaultdict(set)
    
    for field_info in fields:
        model = field_info['model']
        related = field_info['related']
        
        # Parse the related path to find referenced model
        parts = related.split('.')
        if len(parts) >= 2:
            # First part is the field that references another model
            first_field = parts[0]
            
            # Try to find what model this field points to
            for other in fields:
                if other['model'] == model and other['field'] == first_field:
                    # This is a Many2one or related field
                    if 'Many2one' in str(other):
                        continue
            
            # Add edge in dependency graph
            graph[model].add(related)
    
    return graph

def find_cycles(graph):
    """Find cycles in the dependency graph using DFS."""
    def dfs(node, path, visited):
        if node in path:
            cycle_start = path.index(node)
            return [path[cycle_start:]]
        
        if node in visited:
            return []
        
        visited.add(node)
        path.append(node)
        
        cycles = []
        if node in graph:
            for neighbor in graph[node]:
                cycles.extend(dfs(neighbor, path.copy(), visited))
        
        return cycles
    
    all_cycles = []
    visited = set()
    
    for node in graph:
        if node not in visited:
            cycles = dfs(node, [], visited)
            all_cycles.extend(cycles)
    
    return all_cycles

# Parse planning phase
print("Parsing qaco_planning_phase...")
fields = parse_related_fields("qaco_planning_phase/models")

print(f"\nFound {len(fields)} related fields:")
for f in sorted(fields, key=lambda x: x['model']):
    print(f"  {f['model']}.{f['field']} -> {f['related']}")

# Group by model to find potential circular references
print("\n\nGrouping by model:")
by_model = defaultdict(list)
for f in fields:
    by_model[f['model']].append(f)

for model, model_fields in sorted(by_model.items()):
    print(f"\n{model}:")
    for f in model_fields:
        print(f"  {f['field']} = related='{f['related']}'")
        
        # Check if this creates a potential loop
        parts = f['related'].split('.')
        if len(parts) >= 2:
            # Check if any field in this model has same name as second part
            for other in model_fields:
                if other['field'] == parts[0]:
                    print(f"    ⚠️  POTENTIAL LOOP: {f['field']} uses {parts[0]} which is also a related field!")

