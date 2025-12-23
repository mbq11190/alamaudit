#!/usr/bin/env python3
"""
Safe migration preview: identify problematic registry metadata before upgrades.
This script performs read-only checks and prints (or writes) a JSON report.
It does NOT modify the database.

Usage (run from Odoo venv so Odoo packages are importable):
  python scripts/migration_preview.py -d <dbname> -c C:/path/to/odoo.conf -o C:/temp/migration_preview.json

Alternatively (PowerShell):
  C:/path/to/venv/Scripts/python.exe scripts/migration_preview.py -d mydb -c C:/odoo/odoo.conf -o C:/temp/preview.json

"""

from __future__ import print_function

import argparse
import csv
import json
import os
import re

import odoo
from odoo import SUPERUSER_ID, api


def run_preview(
    db_name,
    config_path=None,
    output_path=None,
    print_summary=False,
    export_csv_dir=None,
):
    if config_path:
        # parse config so addons_path and other settings are available
        odoo.tools.config.parse_config(["-c", config_path])
    # Ensure registry available
    registry = odoo.registry(db_name)
    pattern = re.compile(r"default_order\s*=\s*['\"](?P<expr>[^'\"]+)['\"]", re.I)
    report = {
        "db": db_name,
        "bad_fields": [],
        "bad_views": [],
        "views_with_missing_model": [],
        "summary": {},
    }

    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})
        Model = env["ir.model"]
        Field = env["ir.model.fields"]
        View = env["ir.ui.view"]

        # Load models and fields
        model_records = Model.search([], limit=100000)
        model_names = set(model_records.mapped("model"))

        # Find fields which reference missing models
        all_fields = Field.search([], limit=100000)
        for f in all_fields:
            if not f.model or f.model not in model_names:
                report["bad_fields"].append(
                    {
                        "id": f.id,
                        "name": f.name,
                        "model": f.model,
                        "module": f.module,
                        "model_id": f.model_id.id if f.model_id else None,
                    }
                )

        # Inspect views for default_order referring to missing fields
        all_views = View.search([], limit=100000)
        for v in all_views:
            arch = v.arch_db or v.arch or ""
            m = pattern.search(arch)
            if not m:
                continue
            expr = m.group("expr")
            # Fields are comma-separated expressions like "-create_date, name"
            fields = [
                seg.strip().lstrip("+-").split()[0]
                for seg in expr.split(",")
                if seg.strip()
            ]
            # Get field names for this view.model
            model_fields = (
                set(Field.search([("model", "=", v.model)]).mapped("name"))
                if v.model
                else set()
            )
            missing = [fld for fld in fields if fld not in model_fields]
            if missing:
                report["bad_views"].append(
                    {
                        "view_id": v.id,
                        "name": v.name,
                        "model": v.model,
                        "module": v.module,
                        "default_order": expr,
                        "missing_fields": missing,
                    }
                )

        # Views that reference non-existing models
        for v in all_views:
            if v.model and v.model not in model_names:
                report["views_with_missing_model"].append(
                    {
                        "view_id": v.id,
                        "name": v.name,
                        "model": v.model,
                        "module": v.module,
                    }
                )

        report["summary"] = {
            "total_models": len(model_names),
            "total_fields": len(all_fields),
            "total_views": len(all_views),
            "bad_fields_count": len(report["bad_fields"]),
            "bad_views_count": len(report["bad_views"]),
            "views_with_missing_model_count": len(report["views_with_missing_model"]),
        }

    # Output JSON
    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        print("\nSAFE PREVIEW COMPLETE - report written to:", output_path)
    else:
        print("\nSAFE PREVIEW COMPLETE - results:")
        print(json.dumps(report, indent=2))

    # Human-readable summary (optional)
    if print_summary:
        print("\nSAFE PREVIEW SUMMARY:")
        s = report["summary"]
        print(f"Database: {report['db']}")
        print(
            f"Models: {s['total_models']}, Fields: {s['total_fields']}, Views: {s['total_views']}"
        )
        print(
            f"Bad fields: {s['bad_fields_count']}, Bad views: {s['bad_views_count']}, Views with missing model: {s['views_with_missing_model_count']}"
        )
        if report["bad_fields"]:
            print("\nSample bad fields (first 10):")
            for bf in report["bad_fields"][:10]:
                print(
                    f"  id={bf['id']}, name={bf['name']}, model={bf['model']}, module={bf.get('module')}"
                )
        if report["bad_views"]:
            print("\nSample views with missing default_order fields (first 10):")
            for bv in report["bad_views"][:10]:
                print(
                    f"  view id={bv['view_id']}, name={bv['name']}, model={bv['model']}, missing_fields={bv['missing_fields']}"
                )
        if report["views_with_missing_model"]:
            print("\nViews referencing non-existing models (first 10):")
            for vm in report["views_with_missing_model"][:10]:
                print(
                    f"  view id={vm['view_id']}, name={vm['name']}, model={vm['model']}"
                )

    # Optionally export three CSV files with the affected rows
    if export_csv_dir:
        os.makedirs(export_csv_dir, exist_ok=True)
        # bad_fields
        bf_path = os.path.join(export_csv_dir, "bad_fields.csv")
        with open(bf_path, "w", newline="", encoding="utf-8") as bf_csv:
            writer = csv.DictWriter(
                bf_csv, fieldnames=["id", "name", "model", "module", "model_id"]
            )
            writer.writeheader()
            for row in report["bad_fields"]:
                writer.writerow(
                    {
                        k: row.get(k)
                        for k in ["id", "name", "model", "module", "model_id"]
                    }
                )
        # bad_views
        bv_path = os.path.join(export_csv_dir, "bad_views.csv")
        with open(bv_path, "w", newline="", encoding="utf-8") as bv_csv:
            writer = csv.DictWriter(
                bv_csv,
                fieldnames=[
                    "view_id",
                    "name",
                    "model",
                    "module",
                    "default_order",
                    "missing_fields",
                ],
            )
            writer.writeheader()
            for row in report["bad_views"]:
                writer.writerow(
                    {
                        "view_id": row.get("view_id"),
                        "name": row.get("name"),
                        "model": row.get("model"),
                        "module": row.get("module"),
                        "default_order": row.get("default_order"),
                        "missing_fields": ",".join(row.get("missing_fields") or []),
                    }
                )
        # views_with_missing_model
        vm_path = os.path.join(export_csv_dir, "views_with_missing_model.csv")
        with open(vm_path, "w", newline="", encoding="utf-8") as vm_csv:
            writer = csv.DictWriter(
                vm_csv, fieldnames=["view_id", "name", "model", "module"]
            )
            writer.writeheader()
            for row in report["views_with_missing_model"]:
                writer.writerow(
                    {k: row.get(k) for k in ["view_id", "name", "model", "module"]}
                )
        print(f"\nCSV exports written to: {export_csv_dir}")

    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Safe migration preview for qaco_client_onboarding (read-only)"
    )
    parser.add_argument("-d", "--db", required=True, help="Database name")
    parser.add_argument("-c", "--config", help="Path to Odoo config file (optional)")
    parser.add_argument("-o", "--output", help="Path to output JSON file (optional)")
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Print a human-readable summary to the console in addition to the JSON report",
    )
    parser.add_argument(
        "--export-csv",
        dest="export_csv",
        help="Write CSV exports for affected rows into this directory (optional)",
    )
    args = parser.parse_args()

    print("\n*** SAFE PREVIEW - NO CHANGES WILL BE MADE TO THE DATABASE ***\n")
    run_preview(
        args.db,
        args.config,
        args.output,
        print_summary=args.summary,
        export_csv_dir=args.export_csv,
    )
