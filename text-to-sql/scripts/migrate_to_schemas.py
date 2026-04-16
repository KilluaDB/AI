#!/usr/bin/env python3
"""
Migrate PostgreSQL tables from the flat 'public' schema into one schema per db_id.

Usage:
    python scripts/migrate_to_schemas.py \
        --tables_json ./data/foo/test_tables.json \
        [--tables_json ./data/bird-psql/dev_tables.json] \
        [--dry_run]

The script reads table_names_original from each db_id entry in the given
tables.json file(s), then for each db_id:
  1. CREATE SCHEMA IF NOT EXISTS <db_id>;
  2. ALTER TABLE public.<table> SET SCHEMA <db_id>;

Tables already in the target schema (or missing from public) are skipped.
Tables in public that aren't mapped to any db_id are reported at the end.

Pass --dry_run to print the SQL without executing it.
"""
import argparse
import json
import os
import sys

import psycopg2


def build_mapping(tables_json_paths):
    """Return {db_id: [table_name_lower, ...]} from one or more tables.json files."""
    mapping = {}
    for path in tables_json_paths:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        for entry in data:
            db_id = entry["db_id"]
            tables = [t.lower() for t in entry["table_names_original"]]
            if db_id in mapping:
                existing = set(mapping[db_id])
                existing.update(tables)
                mapping[db_id] = sorted(existing)
            else:
                mapping[db_id] = tables
    return mapping


def get_public_tables(cursor):
    cursor.execute("""
        SELECT table_name FROM information_schema.tables
        WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
    """)
    return {row[0] for row in cursor.fetchall()}


def get_existing_schemas(cursor):
    cursor.execute("SELECT schema_name FROM information_schema.schemata")
    return {row[0] for row in cursor.fetchall()}


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--tables_json", action="append", required=True,
                        help="Path to a tables.json file (can be repeated)")
    parser.add_argument("--dry_run", action="store_true",
                        help="Print SQL without executing")
    args = parser.parse_args()

    mapping = build_mapping(args.tables_json)
    print(f"Loaded mapping: {len(mapping)} db_ids, "
          f"{sum(len(v) for v in mapping.values())} table entries")

    conn = psycopg2.connect(
        host=os.environ.get("PG_HOST", "localhost"),
        port=int(os.environ.get("PG_PORT", "5432")),
        dbname=os.environ.get("PG_DATABASE", "BIRD"),
        user=os.environ.get("PG_USER", "postgres"),
        password=os.environ.get("PG_PASSWORD", "postgres"),
    )
    conn.autocommit = True
    cur = conn.cursor()

    public_tables = get_public_tables(cur)
    existing_schemas = get_existing_schemas(cur)
    print(f"Tables currently in public: {len(public_tables)}")

    moved = 0
    skipped = 0
    mapped_tables = set()

    for db_id, tables in sorted(mapping.items()):
        # Create schema
        sql_schema = f'CREATE SCHEMA IF NOT EXISTS "{db_id}";'
        print(f"\n-- {db_id} ({len(tables)} tables)")
        print(sql_schema)
        if not args.dry_run:
            cur.execute(sql_schema)

        for table in tables:
            mapped_tables.add(table)
            if table not in public_tables:
                print(f"  -- SKIP {table} (not in public)")
                skipped += 1
                continue
            sql_move = f'ALTER TABLE public."{table}" SET SCHEMA "{db_id}";'
            print(f"  {sql_move}")
            if not args.dry_run:
                try:
                    cur.execute(sql_move)
                    moved += 1
                except psycopg2.Error as e:
                    print(f"  -- ERROR: {e.pgerror or e}")
                    skipped += 1
            else:
                moved += 1

    unmapped = public_tables - mapped_tables
    if unmapped:
        print(f"\n-- WARNING: {len(unmapped)} tables in public not mapped to any db_id:")
        for t in sorted(unmapped):
            print(f"--   {t}")

    print(f"\nDone: {moved} moved, {skipped} skipped")
    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
