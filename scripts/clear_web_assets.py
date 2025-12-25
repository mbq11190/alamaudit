"""Clear common Odoo web assets directories (safe mode by default).

Usage:
  python scripts/clear_web_assets.py          # dry-run
  python scripts/clear_web_assets.py --confirm  # actually delete

This script will attempt to identify common Odoo asset directories and
remove their contents. It is conservative and requires --confirm to perform
removal to avoid accidental deletions on developer machines.
"""
import argparse
import os
import shutil
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--confirm", action="store_true", help="Actually delete files. Without this flag the script only prints what would be deleted")
args = parser.parse_args()

candidates = []
# Linux/macOS default
candidates.append(Path.home() / ".local" / "share" / "Odoo" / "web" / "assets")
# Some setups use ~/.local/share/Odoo/filestore/<db>/addons_web/static/ or similar; but assets dir above is primary
# Windows (Local AppData)
local_appdata = os.getenv("LOCALAPPDATA")
if local_appdata:
    candidates.append(Path(local_appdata) / "Odoo" / "web" / "assets")

# WSL or alternative paths (common in docker/staging)
candidates.append(Path("/var" ) / "lib" / "odoo" / "web" / "assets")

found = []
for p in candidates:
    if p.exists() and p.is_dir():
        found.append(p)

if not found:
    print("No known Odoo assets directories found. Nothing to do.")
    raise SystemExit(0)

print("Found the following Odoo asset directories:")
for p in found:
    print(" - ", p)

if not args.confirm:
    print("\nDry run mode: no files will be removed. Re-run with --confirm to perform deletion.")
    raise SystemExit(0)

# Perform deletion of directory contents
for p in found:
    try:
        for child in p.iterdir():
            try:
                if child.is_dir():
                    shutil.rmtree(child)
                else:
                    child.unlink()
            except Exception as exc:
                print(f"Failed to remove {child}: {exc}")
        print(f"Cleared assets in {p}")
    except Exception as exc:
        print(f"Failed to list or clear {p}: {exc}")

print("Done.")