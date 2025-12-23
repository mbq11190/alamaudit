"""Restore problematic ir_model_fields rows from backup_problematic_ir_model_fields.

Usage (from repo root):
  python scripts/restore_problematic_fields.py --db <dbname> --user <dbuser> --host <host> --port <port> --ids 123,124

It can be run via psql as well by executing the SQL produced by functions in dry-run mode.

Important: make a DB backup before using this script.
"""

import argparse
import psycopg2
import psycopg2.extras
import sys
from typing import List


def get_columns(cur, table_name):
    cur.execute(
        "SELECT column_name FROM information_schema.columns WHERE table_name=%s ORDER BY ordinal_position",
        (table_name,),
    )
    return [r[0] for r in cur.fetchall()]


def restore_fields(cur, ids: List[int], dry_run: bool = False, force: bool = False):
    if not ids:
        return {"restored": [], "skipped": []}
    placeholders = ",".join(["%s"] * len(ids))
    # Fetch backup rows
    cur.execute(
        f"SELECT * FROM backup_problematic_ir_model_fields WHERE id IN ({placeholders})",
        tuple(ids),
    )
    backups = cur.fetchall()
    if not backups:
        return {"restored": [], "skipped": ids}

    cols = get_columns(cur, "ir_model_fields")
    col_list = ", ".join(cols)
    restored = []
    skipped = []

    for b in backups:
        bid = b[0]
        # Check if ir_model_fields already has row with same id
        cur.execute("SELECT id, model, name FROM ir_model_fields WHERE id=%s", (bid,))
        existing = cur.fetchone()
        if existing:
            # update existing row with backup values
            if dry_run:
                skipped.append((bid, "would_update_existing"))
                continue
            # Build update set from backup row
            set_clauses = []
            params = []
            for i, cname in enumerate(cols):
                if cname == "id":
                    continue
                set_clauses.append(f"{cname} = %s")
                params.append(b[i])
            params.append(bid)
            cur.execute(
                f"UPDATE ir_model_fields SET {', '.join(set_clauses)} WHERE id = %s",
                tuple(params),
            )
            # log
            cur.execute(
                "INSERT INTO qaco_problematic_fields_migration_log (field_id, model, name, relation, ttype, action, created_at) VALUES (%s,%s,%s,%s,%s,%s,now())",
                (bid, b[cols.index('model')], b[cols.index('name')], b[cols.index('relation')], b[cols.index('ttype')], 'restored'),
            )
            restored.append(bid)
            continue
        # If there's an existing field with same model+name but different id -> conflict
        cur.execute("SELECT id FROM ir_model_fields WHERE model=%s AND name=%s", (b[cols.index('model')], b[cols.index('name')]))
        conflict = cur.fetchone()
        if conflict and not force:
            skipped.append((bid, 'conflict_model_name'))
            continue
        if dry_run:
            skipped.append((bid, 'dry_run'))
            continue
        # If conflict and force -> delete conflicting row then insert backup
        if conflict and force:
            cur.execute("DELETE FROM ir_model_fields WHERE id=%s", (conflict[0],))
        # Insert row directly using column list
        # Use explicit insertion to preserve original id
        values = [b[i] for i in range(len(cols))]
        placeholders = ",".join(["%s"] * len(cols))
        cur.execute(f"INSERT INTO ir_model_fields ({col_list}) VALUES ({placeholders})", tuple(values))
        cur.execute(
            "INSERT INTO qaco_problematic_fields_migration_log (field_id, model, name, relation, ttype, action, created_at) VALUES (%s,%s,%s,%s,%s,%s,now())",
            (bid, b[cols.index('model')], b[cols.index('name')], b[cols.index('relation')], b[cols.index('ttype')], 'restored'),
        )
        restored.append(bid)

    return {"restored": restored, "skipped": skipped}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--db", required=True)
    p.add_argument("--user", required=True)
    p.add_argument("--host", default="localhost")
    p.add_argument("--port", default=5432, type=int)
    p.add_argument("--ids", required=True, help="Comma separated backup row ids to restore")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--force", action="store_true", help="If conflict on model+name exists, delete and overwrite")
    args = p.parse_args()

    ids = [int(x.strip()) for x in args.ids.split(",") if x.strip()]
    conn = psycopg2.connect(dbname=args.db, user=args.user, host=args.host, port=args.port)
    cur = conn.cursor()
    try:
        res = restore_fields(cur, ids, dry_run=args.dry_run, force=args.force)
        if args.dry_run:
            conn.rollback()
            print("Dry run results:", res)
        else:
            conn.commit()
            print("Restoration results:", res)
    finally:
        cur.close()
        conn.close()


if __name__ == '__main__':
    main()
