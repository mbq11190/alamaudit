"""Static accessibility checks for XML views.
- <i class="fa..."> should have a title attribute
- <span class="fa..."> should have a title attribute or text
- <a class="btn" should have role="button"
Exits non-zero if any issues found.
"""
import glob
import re
import sys
from xml.etree import ElementTree as ET

issues = []
for f in glob.glob('**/views/*.xml', recursive=True):
    try:
        tree = ET.parse(f)
    except Exception:
        continue
    for elem in tree.findall('.//i'):
        cls = elem.get('class','')
        if 'fa' in cls and not elem.get('title'):
            issues.append((f, ET.tostring(elem, encoding='unicode')))
    for elem in tree.findall('.//span'):
        cls = elem.get('class','')
        if 'fa' in cls and not (elem.get('title') or (elem.text and elem.text.strip())):
            issues.append((f, ET.tostring(elem, encoding='unicode')))
    for elem in tree.findall('.//a'):
        cls = elem.get('class','')
        if 'btn' in cls and not elem.get('role'):
            issues.append((f, ET.tostring(elem, encoding='unicode')))

print('Accessibility issues found:', len(issues))
for f, s in issues:
    # Print a safe, ASCII-only summary (avoid raw element Unicode that can break Windows consoles)
    try:
        # s might contain unicode; instead print tag, class and title attributes
        import re
        m = re.search(r'<(i|span|a)\b([^>]*)>', s)
        if m:
            tag = m.group(1)
            attrs = m.group(2)
            # extract class/title/role
            cls = ''
            title = ''
            role = ''
            for a in attrs.split():
                if a.startswith('class='):
                    cls = a
                if a.startswith('title='):
                    title = a
                if a.startswith('role='):
                    role = a
            print(f"{f} - <{tag}> {cls} {title} {role}")
        else:
            print(f"{f} - {s}")
    except Exception:
        print(f"{f} - (issue)")
if issues:
    sys.exit(1)
sys.exit(0)
