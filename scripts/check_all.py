import sys
import xml.etree.ElementTree as ET
import glob
import py_compile

errs = 0
# Check XML views
files=glob.glob('**/views/*.xml', recursive=True)
for f in files:
    try:
        ET.parse(f)
    except Exception as e:
        print('XML PARSE ERROR:', f, e)
        errs += 1

# Check python compile for module files
py_files = glob.glob('**/*.py', recursive=True)
for p in py_files:
    try:
        py_compile.compile(p, doraise=True)
    except Exception as e:
        print('PYTHON SYNTAX ERROR:', p, e)
        errs += 1

if errs:
    print('Checks failed: errors=', errs)
    sys.exit(2)
print('Checks passed')
