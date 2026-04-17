import os
import re
import psycopg2


def normalize_pg_sql(sql):
    """
    Strip double-quotes from simple identifiers so PostgreSQL lowercases them
    to match the actual column names. Identifiers containing spaces, parens,
    hyphens, %, or / stay quoted (e.g. "Enrollment (K-12)").
    """
    def _unquote(match):
        ident = match.group(1)
        if re.search(r'[\s()\-/%]', ident):
            return match.group(0)
        return ident

    return re.sub(r'"([^"]+)"', _unquote, sql)


def get_pg_connection(autocommit=True, schema=None):
    """Connect to PostgreSQL. If *schema* is given, set search_path to it."""
    conn = psycopg2.connect(
        host=os.environ.get("PG_HOST", "localhost"),
        port=int(os.environ.get("PG_PORT", "5432")),
        dbname=os.environ.get("PG_DATABASE", "BIRD"),
        user=os.environ.get("PG_USER", "postgres"),
        password=os.environ.get("PG_PASSWORD", "postgres"),
    )
    conn.autocommit = autocommit
    if schema:
        cur = conn.cursor()
        cur.execute("SET search_path TO %s", (schema,))
        cur.close()
    return conn


def get_pg_schema(schema_name='public'):
    """
    Return schema dict: {table_name: [col1, col2, ...], ...}
    using information_schema instead of SQLite's PRAGMA table_info.
    *schema_name* is the PostgreSQL schema (typically the db_id).
    """
    conn = get_pg_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT table_name FROM information_schema.tables
        WHERE table_schema = %s AND table_type = 'BASE TABLE'
    """, (schema_name,))
    tables = [row[0].lower() for row in cursor.fetchall()]
    schema = {}
    for table in tables:
        cursor.execute("""
            SELECT column_name FROM information_schema.columns
            WHERE table_schema = %s AND table_name = %s
            ORDER BY ordinal_position
        """, (schema_name, table))
        schema[table] = [row[0].lower() for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return schema
