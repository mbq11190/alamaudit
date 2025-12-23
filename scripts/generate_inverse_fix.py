"""Generate an ORM-correct fix for missing inverse fields.

Usage:
  python scripts/generate_inverse_fix.py --one2many-file path/to/file.py --line 123
  or
  python scripts/generate_inverse_fix.py --comodel 'qaco.onboarding.independence.threat' --inverse 'onboarding_id' --parent 'qaco.client.onboarding' --module my_module

This script does NOT apply changes automatically. It generates a patch file under patches/<module>/ and prints a suggested before/after snippet.
"""

import argparse
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def suggest_many2one(comodel, inverse, parent_model):
    snippet = f"""
# Add to model that defines _name = '{comodel}'
{inverse} = fields.Many2one(
    '{parent_model}',
    string='Onboarding',
    ondelete='cascade',
    index=True,
)
"""
    return textwrap.dedent(snippet)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--comodel", help="Model _name for child model (comodel)")
    p.add_argument("--inverse", help="Inverse field name expected (e.g. onboarding_id)")
    p.add_argument("--parent", help="Parent model _name (e.g. qaco.client.onboarding)")
    p.add_argument("--module", help="Module name owning the comodel (for patch path)")
    p.add_argument("--file", help="Specific file to patch (optional)")
    args = p.parse_args()

    if not (args.comodel and args.inverse and args.parent):
        print("Provide --comodel, --inverse and --parent")
        return

    suggestion = suggest_many2one(args.comodel, args.inverse, args.parent)
    print("\nSuggested addition:\n")
    print(suggestion)

    if args.module:
        patch_dir = ROOT / "patches" / args.module
        patch_dir.mkdir(parents=True, exist_ok=True)
        patch_file = (
            patch_dir / f'add_{args.inverse}_to_{args.comodel.replace(".","_")}.patch'
        )
        content = f"""# Patch: add {args.inverse} Many2one to model {args.comodel}
# Apply by editing the file where the model {args.comodel} is defined.

{suggestion}
"""
        patch_file.write_text(content, encoding="utf-8")
        print(f"Patch file generated: {patch_file}")


if __name__ == "__main__":
    main()
