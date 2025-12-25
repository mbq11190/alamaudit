"""Static checks for SCSS files to prevent Odoo 17 asset compilation failures.

Checks performed:
- No usage of deprecated '@import' for importing bootstrap/variables
- Braces balance check (count '{' == '}')
- If $o- variables are used, ensure "@use 'web.variables' as *;" present
- Ensure files declared in manifests exist
- Report warnings and errors; exit non-zero on errors
"""
import glob
import re
import sys
from pathlib import Path

errors = []
warnings = []

# 1) Scan scss files
scss_files = glob.glob("**/*.scss", recursive=True)
for f in scss_files:
    try:
        txt = Path(f).read_text(encoding="utf-8")
    except Exception as e:
        errors.append(f"Failed to read {f}: {e}")
        continue
    if "@import" in txt:
        # flag deprecated import usage
        errors.append(f"Deprecated '@import' found in {f}; use '@use' and web variables instead")
    # check braces balance
    open_braces = txt.count("{")
    close_braces = txt.count("}")
    if open_braces != close_braces:
        errors.append(f"Unbalanced braces in {f}: '{{'={open_braces} vs '}}'={close_braces}")
    # check $o- variables usage without web.variables
    if re.search(r"\$o-[A-Za-z0-9_-]+", txt):
        if "@use 'web.variables' as *;" not in txt and "@use \"web.variables\" as *;" not in txt:
            warnings.append(f"File {f} uses $o- variables but does not @use 'web.variables' (may compile if web.variables is provided by bundle)")

# 2) Validate manifest asset declarations point to existing files
manifest_files = glob.glob("**/__manifest__.py", recursive=True)
for mf in manifest_files:
    try:
        content = Path(mf).read_text(encoding="utf-8")
    except Exception as e:
        errors.append(f"Failed to read manifest {mf}: {e}")
        continue
    # crude parse for assets list
    for line in content.splitlines():
        line = line.strip()
        # match typical asset paths 'module/static/src/..'
        if re.search(r"['\"][\w\-./]+\.scss['\"]", line):
            m = re.search(r"['\"]([\w\-./]+\.scss)['\"]", line)
            if m:
                path = Path(mf).parent / m.group(1)
                if not path.exists():
                    errors.append(f"Manifest {mf} references missing scss asset: {m.group(1)}")

# Output results
print(f"SCSS files scanned: {len(scss_files)}")
if warnings:
    print("Warnings:")
    for w in warnings:
        print(" - ", w)
if errors:
    print("Errors (fatal):")
    for e in errors:
        print(" - ", e)
    sys.exit(1)
print("SCSS static checks passed")
