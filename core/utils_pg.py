# -*- coding: utf-8 -*-
"""
PostgreSQL-adapted utility functions for text-to-SQL generation.
This module provides helper functions that don't depend on SQLite.
"""
import os
import re
import json
import time
import psycopg2
from typing import Dict, List, Any


def is_valid_date(date_str):
    """Check if string is a valid date in YYYY-MM-DD format."""
    if not isinstance(date_str, str):
        return False
    date_str = date_str.split()[0]
    if len(date_str) != 10:
        return False
    pattern = r'^\d{4}-\d{2}-\d{2}$'
    if re.match(pattern, date_str):
        year, month, day = map(int, date_str.split('-'))
        if year < 1 or month < 1 or month > 12 or day < 1 or day > 31:
            return False
        return True
    return False


def is_valid_date_column(col_value_lst):
    """Check if all values in a column are valid dates."""
    for col_value in col_value_lst:
        if not is_valid_date(col_value):
            return False
    return True


def is_email(string):
    """Check if string is an email address."""
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return bool(re.match(pattern, string))


def extract_world_info(message_dict: dict):
    """Extract relevant info from message for logging."""
    info_dict = {}
    info_dict['idx'] = message_dict.get('idx', 0)
    info_dict['db_id'] = message_dict.get('db_id', '')
    info_dict['query'] = message_dict.get('query', '')
    info_dict['evidence'] = message_dict.get('evidence', '')
    info_dict['difficulty'] = message_dict.get('difficulty', '')
    info_dict['ground_truth'] = message_dict.get('ground_truth', '')
    info_dict['send_to'] = message_dict.get('send_to', '')
    return info_dict


def replace_multiple_spaces(text):
    """Replace multiple spaces with a single space."""
    pattern = r'\s+'
    return re.sub(pattern, ' ', text)


def extract_table_names(sql_query):
    """Extract table names from SQL query."""
    sql_query = sql_query.replace('"', '').replace('`', '')
    table_names = re.findall(r'FROM\s+([\w]+)', sql_query, re.IGNORECASE) + \
                  re.findall(r'JOIN\s+([\w]+)', sql_query, re.IGNORECASE)
    return set(table_names)


def get_pg_connection(db_config: Dict[str, Any]):
    """Create PostgreSQL connection from config dict."""
    return psycopg2.connect(
        host=db_config['host'],
        port=db_config['port'],
        user=db_config['user'],
        password=db_config['password'],
        dbname=db_config['dbname']
    )


def get_used_tables(sql: str, db_config: Dict[str, Any]) -> dict:
    """
    Get tables used in SQL query and their columns.
    
    Args:
        sql: SQL query string
        db_config: PostgreSQL connection config
    
    Returns:
        Dict mapping table names to their columns
    """
    table_names = extract_table_names(sql)
    sch = {}
    
    conn = get_pg_connection(db_config)
    cursor = conn.cursor()
    
    for table_name in table_names:
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = %s AND table_schema = 'public'
            ORDER BY ordinal_position
        """, (table_name,))
        columns = cursor.fetchall()
        column_names = [col[0] for col in columns]
        sch[table_name] = {
            "chosen columns": column_names,
            "discarded columns": []
        }
    
    cursor.close()
    conn.close()
    return sch


def get_all_tables(db_config: Dict[str, Any]) -> dict:
    """
    Get all tables and their columns from PostgreSQL database.
    
    Args:
        db_config: PostgreSQL connection config
    
    Returns:
        Dict mapping table names to their columns
    """
    conn = get_pg_connection(db_config)
    cursor = conn.cursor()
    
    # Get all table names
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
    """)
    tables = cursor.fetchall()
    table_names = [t[0] for t in tables]
    
    sch = {}
    for table_name in table_names:
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = %s AND table_schema = 'public'
            ORDER BY ordinal_position
        """, (table_name,))
        columns = cursor.fetchall()
        column_names = [col[0] for col in columns]
        sch[table_name] = {
            "chosen columns": column_names,
            "discarded columns": []
        }
    
    cursor.close()
    conn.close()
    return sch


def get_schema_info(db_config: Dict[str, Any]) -> Dict[str, List[Dict]]:
    """
    Get complete schema information from PostgreSQL database.
    
    Args:
        db_config: PostgreSQL connection config
    
    Returns:
        Dict mapping table names to list of column info dicts
    """
    conn = get_pg_connection(db_config)
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
    """)
    tables = [row[0] for row in cursor.fetchall()]
    
    schema = {}
    for table in tables:
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = %s AND table_schema = 'public'
            ORDER BY ordinal_position
        """, (table,))
        
        columns = []
        for row in cursor.fetchall():
            columns.append({
                'column_name': row[0],
                'data_type': row[1],
                'is_nullable': row[2],
                'column_default': row[3]
            })
        schema[table] = columns
    
    cursor.close()
    conn.close()
    return schema


def check_selector_response(json_data: Dict) -> bool:
    """Validate selector response format."""
    FLAGS = ['keep_all', 'drop_all']
    for k, v in json_data.items():
        if isinstance(v, str):
            if v not in FLAGS:
                print(f"error: invalid table flag: {v}")
                return False
        elif isinstance(v, list):
            pass
        else:
            print(f"error: invalid flag type: {v}")
            return False
    return True


def parse_json(text: str) -> dict:
    """Parse JSON from LLM response."""
    start = text.find("```json")
    end = text.find("```", start + 7)
    
    if start != -1 and end != -1:
        json_string = text[start + 7: end]
        try:
            json_data = json.loads(json_string)
            if check_selector_response(json_data):
                return json_data
        except json.JSONDecodeError:
            print(f"error: parse json error!")
            print(f"json_string: {json_string}")
    
    return {}


def parse_sql_from_string(input_string: str) -> str:
    """
    Extract and clean SQL from LLM response.
    Aggressively strips markdown formatting, comments, and non-SELECT statements.
    """
    if not input_string or not input_string.strip():
        return "error: Empty input string"
    
    sql = input_string.strip()
    
    # Step 1: Try to extract from markdown code blocks first
    sql_pattern = r'```(?:sql)?\s*(.*?)```'
    matches = re.findall(sql_pattern, sql, re.DOTALL | re.IGNORECASE)
    if matches:
        # Get the last SQL block (usually the final answer)
        sql = matches[-1].strip()
    
    # Step 2: Remove any remaining markdown artifacts
    sql = re.sub(r'^```\w*\s*', '', sql)  # Remove opening ```sql or ```
    sql = re.sub(r'\s*```$', '', sql)      # Remove closing ```
    sql = sql.strip('`')                    # Remove any stray backticks
    
    # Step 3: Remove SQL comments (both -- and /* */ style)
    sql = re.sub(r'--[^\n]*\n?', '', sql)  # Remove -- comments
    sql = re.sub(r'/\*.*?\*/', '', sql, flags=re.DOTALL)  # Remove /* */ comments
    
    # Step 4: Remove common LLM preamble/postamble text
    preamble_patterns = [
        r'^(?:Here\'s?\s+(?:the\s+)?(?:corrected\s+)?(?:SQL\s+)?(?:query)?:?\s*)',
        r'^(?:The\s+(?:corrected\s+)?SQL\s+(?:query\s+)?is:?\s*)',
        r'^(?:SQL\s*:?\s*)',
        r'^(?:Answer\s*:?\s*)',
        r'^(?:Result\s*:?\s*)',
    ]
    for pattern in preamble_patterns:
        sql = re.sub(pattern, '', sql, flags=re.IGNORECASE)
    
    # Step 5: If there are multiple statements, extract only SELECT statements
    # Split by semicolon but be careful with strings
    statements = []
    current = []
    in_string = False
    string_char = None
    
    for char in sql:
        if char in ("'", '"') and not in_string:
            in_string = True
            string_char = char
        elif char == string_char and in_string:
            in_string = False
            string_char = None
        
        if char == ';' and not in_string:
            stmt = ''.join(current).strip()
            if stmt:
                statements.append(stmt)
            current = []
        else:
            current.append(char)
    
    # Don't forget the last statement
    last_stmt = ''.join(current).strip()
    if last_stmt:
        statements.append(last_stmt)
    
    # Step 6: Filter to only SELECT statements (ignore INSERT, UPDATE, DELETE, CREATE, etc.)
    select_statements = []
    for stmt in statements:
        stmt_upper = stmt.upper().strip()
        if stmt_upper.startswith('SELECT') or stmt_upper.startswith('WITH'):
            select_statements.append(stmt)
    
    # Step 7: Return the last SELECT statement (usually the final answer)
    if select_statements:
        final_sql = select_statements[-1].strip()
        # Clean up whitespace
        final_sql = re.sub(r'\s+', ' ', final_sql)
        return final_sql
    
    # Step 8: If no SELECT found, check if the whole thing looks like a SELECT
    sql_clean = re.sub(r'\s+', ' ', sql).strip()
    if sql_clean.upper().startswith('SELECT') or sql_clean.upper().startswith('WITH'):
        return sql_clean
    
    # Step 9: Last resort - return cleaned input if it contains SELECT somewhere
    if 'SELECT' in sql.upper():
        # Try to extract just the SELECT part
        select_match = re.search(r'((?:WITH\s+.*?\s+)?SELECT\s+.+?)(?:;|\Z)', sql, re.IGNORECASE | re.DOTALL)
        if select_match:
            result = select_match.group(1).strip()
            result = re.sub(r'\s+', ' ', result)
            return result
    
    return "error: No valid SELECT statement found in the input"


def clean_sql_output(sql: str) -> str:
    """
    Final cleanup of SQL before returning to API.
    Removes any remaining formatting issues.
    """
    if not sql or sql.startswith('error:'):
        return sql
    
    # Remove markdown
    sql = re.sub(r'^```\w*\s*', '', sql)
    sql = re.sub(r'\s*```$', '', sql)
    sql = sql.strip('`')
    
    # Remove comments
    sql = re.sub(r'--[^\n]*', '', sql)
    sql = re.sub(r'/\*.*?\*/', '', sql, flags=re.DOTALL)
    
    # Normalize whitespace
    sql = re.sub(r'\s+', ' ', sql).strip()
    
    # Remove trailing semicolon (optional, depends on preference)
    # sql = sql.rstrip(';')
    
    return sql


def parse_sql(res: str) -> str:
    """Ensure SQL starts with SELECT."""
    if 'SELECT' not in res and 'select' not in res:
        res = 'SELECT ' + res
    res = res.replace('\n', ' ')
    return res.strip()


def add_prefix(sql):
    """Add SELECT prefix if missing."""
    if not sql.startswith('SELECT') and not sql.startswith('select'):
        sql = 'SELECT ' + sql
    return sql


def read_txt_file(path):
    """Read text file into list of lines."""
    with open(path, 'r', encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip() != '']


def load_json_file(path):
    """Load JSON file."""
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_jsonl_file(path):
    """Load JSONL file."""
    with open(path, 'r', encoding='utf-8') as f:
        data = []
        for line in f:
            js_str = line.strip()
            if js_str:
                data.append(json.loads(js_str))
        return data


def save_json_file(path, data):
    """Save data to JSON file."""
    os.makedirs(os.path.dirname(path), exist_ok=True) if os.path.dirname(path) else None
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def save_jsonl_file(path, data):
    """Save data to JSONL file."""
    os.makedirs(os.path.dirname(path), exist_ok=True) if os.path.dirname(path) else None
    with open(path, 'w', encoding='utf-8') as f:
        for js in data:
            f.write(json.dumps(js, ensure_ascii=False) + '\n')


def append_file(path, string_lst):
    """Append lines to file."""
    os.makedirs(os.path.dirname(path), exist_ok=True) if os.path.dirname(path) else None
    with open(path, 'a+', encoding='utf-8') as f:
        for string in string_lst:
            if string[-1] != '\n':
                string += '\n'
            f.write(string)


def format_schema_for_prompt(schema: Dict[str, List[Dict]]) -> str:
    """
    Format schema dict into a string suitable for LLM prompts.
    
    Args:
        schema: Dict from get_schema_info()
    
    Returns:
        Formatted schema string
    """
    lines = []
    for table_name, columns in schema.items():
        lines.append(f"# Table: {table_name}")
        col_lines = []
        for col in columns:
            col_name = col['column_name']
            col_type = col['data_type']
            nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
            col_lines.append(f"  ({col_name}, {col_type}, {nullable})")
        lines.append("[\n" + "\n".join(col_lines) + "\n]")
        lines.append("")
    
    return "\n".join(lines)


def execute_sql_pg(sql: str, db_config: Dict[str, Any], timeout: int = 30) -> Dict:
    """
    Execute SQL on PostgreSQL and return results.
    
    Args:
        sql: SQL query string
        db_config: PostgreSQL connection config
        timeout: Query timeout in seconds
    
    Returns:
        Dict with 'data', 'error', and 'columns' keys
    """
    try:
        conn = get_pg_connection(db_config)
        cursor = conn.cursor()
        
        # Set statement timeout
        cursor.execute(f"SET statement_timeout = {timeout * 1000}")
        
        cursor.execute(sql)
        
        # Check if query returns data
        if cursor.description:
            columns = [desc[0] for desc in cursor.description]
            data = cursor.fetchall()
            result = {
                'data': data,
                'columns': columns,
                'error': None
            }
        else:
            result = {
                'data': None,
                'columns': None,
                'error': None,
                'rowcount': cursor.rowcount
            }
        
        cursor.close()
        conn.close()
        return result
        
    except psycopg2.Error as e:
        return {
            'data': None,
            'columns': None,
            'error': str(e.pgerror) if e.pgerror else str(e)
        }
    except Exception as e:
        return {
            'data': None,
            'columns': None,
            'error': str(e)
        }
