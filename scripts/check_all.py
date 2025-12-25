import glob
import py_compile
import sys
import xml.etree.ElementTree as ET

errs = 0
# Check XML views
files = glob.glob("**/views/*.xml", recursive=True)
for f in files:
    try:
        ET.parse(f)
    except Exception as e:
        print("XML PARSE ERROR:", f, e)
        errs += 1

# Check python compile for module files
py_files = glob.glob("**/*.py", recursive=True)
for p in py_files:
    try:
        py_compile.compile(p, doraise=True)
    except Exception as e:
        print("PYTHON SYNTAX ERROR:", p, e)
        errs += 1

# Run SCSS static checks
try:
    import scripts.check_scss as scss_check
    scss_check
    print('Running SCSS static checks...')
    from importlib import reload

    reload(scss_check)
except Exception:
    print('SCSS check script not importable; running as subprocess instead')
    import subprocess

    r = subprocess.run(["python", "scripts/check_scss.py"], capture_output=False)
    if r.returncode != 0:
        print('SCSS static checks failed')
        errs += 1

# Run accessibility checks for views
try:
    import scripts.check_view_accessibility as acc_check
    acc_check
    print('Running view accessibility checks...')
    from importlib import reload

    reload(acc_check)
except Exception:
    print('Accessibility check script not importable; running as subprocess instead')
    import subprocess

    r = subprocess.run(["python", "scripts/check_view_accessibility.py"], capture_output=False)
    if r.returncode != 0:
        print('View accessibility checks failed')
        errs += 1
if errs:
    print("Checks failed: errors=", errs)
    sys.exit(2)
print("Checks passed")
