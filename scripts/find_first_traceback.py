#!/usr/bin/env python3
"""Extract the first Python traceback from an Odoo upgrade log file.
Usage: python scripts/find_first_traceback.py /path/to/upgrade.log
Prints the traceback block (Traceback ... stack ... exception) and exits with 0 if found, non-zero otherwise.
"""
import sys
import re

if len(sys.argv) < 2:
    print("Usage: python scripts/find_first_traceback.py /path/to/upgrade.log", file=sys.stderr)
    sys.exit(2)

path = sys.argv[1]
text = open(path, 'r', encoding='utf-8', errors='ignore').read()

# Find the first occurrence of a Python traceback
tb_start = text.find('Traceback (most recent call last):')
if tb_start == -1:
    # sometimes Odoo logs show 'Traceback (most recent call last)' without trailing colon
    m = re.search(r'Traceback \(most recent call last\)', text)
    if m:
        tb_start = m.start()

if tb_start == -1:
    print('No Python traceback found in file', file=sys.stderr)
    sys.exit(1)

# Extract from tb_start to the next blank line followed by a non-indented line that is not part of traceback
rest = text[tb_start:]
lines = rest.splitlines()
block = []
for i, ln in enumerate(lines):
    block.append(ln)
    # A heuristic: End when we find a line that looks like an Odoo log level header or an unrelated WARNING/ERROR
    if re.match(r"^[A-Z]{2,}\d{2,} .*|^\[.*\] .*|^WARNING:|^ERROR:|^CRITICAL:|^INFO:|^DEBUG:", ln):
        # Stop but include that line as context
        break

print('\n'.join(block))
sys.exit(0)
