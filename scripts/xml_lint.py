import sys
import xml.etree.ElementTree as ET
from pathlib import Path

files = [
    r"c:\Users\ADMIN\Documents\GitHub\alamaudit\qaco_client_onboarding\views\client_onboarding_form.xml",
    r"c:\Users\ADMIN\Documents\GitHub\alamaudit\qaco_client_onboarding\views\onboarding_template_views.xml",
]

ok = True
for p in files:
    try:
        tree = ET.parse(p)
        print(f"OK: Parsed {p}")
    except ET.ParseError as e:
        print(f"ERROR parsing {p}: {e}")
        ok = False
    except Exception as e:
        print(f"ERROR reading {p}: {e}")
        ok = False

if not ok:
    sys.exit(2)
print('XML lint completed.')
