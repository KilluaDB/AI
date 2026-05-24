# -*- coding: utf-8 -*-
"""
PostgreSQL-adapted utility functions for text-to-SQL generation.
This module provides helper functions that don't depend on SQLite.
"""
import os
import re
import json
import time
import psycopg2  # pyright: ignore[reportMissingModuleSource]
from typing import Dict, List, Any
from core.const import subq_pattern


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

def parse_analysis_from_string(input_string):
    pattern = r'\{.*?\}'
    match = re.findall(pattern, input_string, re.DOTALL)[-1]
    json_dict = json.loads(match)
    analysis=json_dict['reasoning']
    label = True if 'yes' in json_dict['judgment'].lower() else False
    return label, analysis

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


def get_used_tables(sql: str, db_config: Dict[str, Any], schema: str = 'public') -> dict:
    """
    Get tables used in SQL query and their columns.
    
    Args:
        sql: SQL query string
        db_config: PostgreSQL connection config
        schema: PostgreSQL schema name (typically the db_id)
    
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
            WHERE table_name = %s AND table_schema = %s
            ORDER BY ordinal_position
        """, (table_name, schema))
        columns = cursor.fetchall()
        column_names = [col[0] for col in columns]
        sch[table_name] = {
            "chosen columns": column_names,
            "discarded columns": []
        }
    
    cursor.close()
    conn.close()
    return sch


def get_all_tables(db_config: Dict[str, Any], schema: str = 'public') -> dict:
    """
    Get all tables and their columns from PostgreSQL database.
    
    Args:
        db_config: PostgreSQL connection config
        schema: PostgreSQL schema name (typically the db_id)
    
    Returns:
        Dict mapping table names to their columns
    """
    conn = get_pg_connection(db_config)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = %s AND table_type = 'BASE TABLE'
    """, (schema,))
    tables = cursor.fetchall()
    table_names = [t[0] for t in tables]
    
    sch = {}
    for table_name in table_names:
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = %s AND table_schema = %s
            ORDER BY ordinal_position
        """, (table_name, schema))
        columns = cursor.fetchall()
        column_names = [col[0] for col in columns]
        sch[table_name] = {
            "chosen columns": column_names,
            "discarded columns": []
        }
    
    cursor.close()
    conn.close()
    return sch


def get_schema_info(db_config: Dict[str, Any], schema_name: str = 'public') -> Dict[str, List[Dict]]:
    """
    Get complete schema information from PostgreSQL database.
    
    Args:
        db_config: PostgreSQL connection config
        schema_name: PostgreSQL schema name (typically the db_id)
    
    Returns:
        Dict mapping table names to list of column info dicts
    """
    conn = get_pg_connection(db_config)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = %s AND table_type = 'BASE TABLE'
    """, (schema_name,))
    tables = [row[0] for row in cursor.fetchall()]
    
    schema = {}
    for table in tables:
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = %s AND table_schema = %s
            ORDER BY ordinal_position
        """, (table, schema_name))
        
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
#######################################################################################################
#######################################################################################################
#######################################################################################################
#######################################################################################################
#######################################################################################################
#######################################################################################################






def rename_file(file_path, new_name):
    """
    给定原文件路径和新文件名，重命名文件

    @param file_path: 原文件路径, 如: /home/user/test.txt
    @param new_name: 新文件名, 如: backup
    @return: 新文件路径
    """
    # 获取文件的目录和后缀名
    dir_name = os.path.dirname(file_path)
    file_name, file_ext = os.path.splitext(os.path.basename(file_path))
    
    # 获取当前时间戳
    timestamp = str(int(time.time()))
    
    # 构建新的文件名
    new_file_name = new_name + '_' + timestamp + file_ext
    
    # 构建新的文件路径
    new_file_path = os.path.join(dir_name, new_file_name)
    
    # 重命名文件
    os.rename(file_path, new_file_path)
    
    return new_file_path


def save_file(path, string_lst):
    """
    保存文件
    :param path: 文件路径 str 类型
    :param string_lst: 字符串列表, 带有换行符
    """
    with open(path, 'w', encoding='utf-8') as f:
        f.writelines(string_lst)
        print(f"save file to {path}")


def parse_sql(res: str) -> str:
    """Only need SQL(startswith `SELECT`) of LLM result"""
    if 'SELECT' not in res and 'select' not in res:
        res = 'SELECT ' + res
    # match = re.search(parse_pattern, res, re.IGNORECASE | re.DOTALL)
    # if match:
    #     sql = match.group().strip()
    #     sql = sql.replace('```', '') # TODO
    #     sql = sql.replace('\n', ' ') # TODO
    #     return True, sql
    # else:
    #     return False, ""
    res = res.replace('\n', ' ')
    return res.strip()


# def parse_sql_from_string(input_string):
#     if not input_string or not input_string.strip():
#         return "error: No SQL found in the input string"

#     text = input_string.strip()

#     # 1) Prefer SQL fenced blocks
#     sql_blocks = re.findall(r"```(?:sql)?\s*(.*?)\s*```", text, re.DOTALL | re.IGNORECASE)
#     if sql_blocks:
#         sql = sql_blocks[-1].strip()
#         if sql:
#             return re.sub(r"\s+", " ", sql).strip()

#     # 2) Remove markdown artifacts / comments and normalize
#     cleaned = text
#     cleaned = re.sub(r"```(?:sql)?", "", cleaned, flags=re.IGNORECASE)
#     cleaned = cleaned.replace("```", "")
#     cleaned = re.sub(r"--[^\n]*", "", cleaned)
#     cleaned = re.sub(r"/\*.*?\*/", "", cleaned, flags=re.DOTALL)
#     cleaned = cleaned.strip()

#     # 3) If model returned raw SQL (common with strict prompts), accept it
#     if re.match(r"(?is)^\s*(with|select)\b", cleaned):
#         return re.sub(r"\s+", " ", cleaned).strip()

#     # 4) Extract first WITH/SELECT statement from mixed text
#     match = re.search(r"(?is)((?:with\b.*?\bselect\b.*?|select\b.*?))(?:;|$)", cleaned)
#     if match:
#         sql = match.group(1).strip()
#         if sql:
#             return re.sub(r"\s+", " ", sql).strip()

#     return "error: No SQL found in the input string"


def parse_single_sql(res: str) -> str:  # if do not need decompose, just one code block is OK!
    """Return SQL in markdown block"""
    lines = res.split('\n')
    iter, start_idx, end_idx = -1, -1, -1
    for idx in range(iter + 1, len(lines)):
        if '```' in lines[idx]:
            start_idx = idx
            break
    if start_idx == -1: return ""
    for idx in range(start_idx + 1, len(lines)):
        if '```' in lines[idx]:
            end_idx = idx
            break
    if end_idx == -1: return f"error: \n{res}"

    return " ".join(lines[start_idx + 1: end_idx])


def parse_qa_pairs(res: str, end_pos=2333) -> list:
    lines = res.split('\n')
    qa_pairs = []
    # end_pos = -1
    # for idx, line in enumerate(lines):
    #     if 'final SQL' in line or 'final sql' in line:
    #         end_pos = idx
    # if end_pos == -1: return []
    end_pos = len(lines) if (end_pos == 2333) else end_pos
    for idx in range(0, end_pos):
        if re.findall(subq_pattern, lines[idx], re.IGNORECASE) != []:
            query = lines[idx]
            start_idx = -1
            for idx2 in range(idx + 1, end_pos):
                if '```' in lines[idx2]:
                    start_idx = idx2
                    break
            if start_idx == -1: return []
            for idx3 in range(start_idx + 1, end_pos):
                if '```' in lines[idx3]:
                    end_idx = idx3
                    break
            if end_idx == -1: return []
            answer = " ".join(lines[start_idx + 1: end_idx])
            qa_pairs.append((str(query), str(answer)))
            idx = end_idx
    return qa_pairs


def parse_subq(res: str) -> list:
    """Only sub questions after decomposition"""
    res = '-- ' + res
    sub_qustions = []
    sub_qustions += res.split('-- ')
    sub_qustions = [q.strip() for q in sub_qustions if len(q) > 1]
    return sub_qustions


def add_prefix(sql):
    if not sql.startswith('SELECT') and not sql.startswith('select'):
        sql = 'SELECT' + sql
    return sql


# Spider data preprocess


CLAUSE_KEYWORDS = ('select', 'from', 'where', 'group', 'order', 'limit', 'intersect', 'union', 'except')
JOIN_KEYWORDS = ('join', 'on', 'as')

WHERE_OPS = ('not', 'between', '=', '>', '<', '>=', '<=', '!=', 'in', 'like', 'is', 'exists')
UNIT_OPS = ('none', '-', '+', "*", '/')
AGG_OPS = ('none', 'max', 'min', 'count', 'sum', 'avg')
TABLE_TYPE = {
    'sql': "sql",
    'table_unit': "table_unit",
}

COND_OPS = ('and', 'or')
SQL_OPS = ('intersect', 'union', 'except')
ORDER_OPS = ('desc', 'asc')


HARDNESS = {
    "component1": ('where', 'group', 'order', 'limit', 'join', 'or', 'like'),
    "component2": ('except', 'union', 'intersect')
}


def get_nestedSQL(sql):
    nested = []
    for cond_unit in sql['from']['conds'][::2] + sql['where'][::2] + sql['having'][::2]:
        if type(cond_unit[3]) is dict:
            nested.append(cond_unit[3])
        if type(cond_unit[4]) is dict:
            nested.append(cond_unit[4])
    if sql['intersect'] is not None:
        nested.append(sql['intersect'])
    if sql['except'] is not None:
        nested.append(sql['except'])
    if sql['union'] is not None:
        nested.append(sql['union'])
    return nested


def has_agg(unit):
    return unit[0] != AGG_OPS.index('none')


def count_agg(units):
    return len([unit for unit in units if has_agg(unit)])


def count_component1(sql):
    count = 0
    if len(sql['where']) > 0:
        count += 1
    if len(sql['groupBy']) > 0:
        count += 1
    if len(sql['orderBy']) > 0:
        count += 1
    if sql['limit'] is not None:
        count += 1
    if len(sql['from']['table_units']) > 0:  # JOIN
        count += len(sql['from']['table_units']) - 1

    ao = sql['from']['conds'][1::2] + sql['where'][1::2] + sql['having'][1::2]
    count += len([token for token in ao if token == 'or'])
    cond_units = sql['from']['conds'][::2] + sql['where'][::2] + sql['having'][::2]
    count += len([cond_unit for cond_unit in cond_units if cond_unit[1] == WHERE_OPS.index('like')])

    return count


def count_component2(sql):
    nested = get_nestedSQL(sql)
    return len(nested)


def count_others(sql):
    count = 0
    # number of aggregation
    agg_count = count_agg(sql['select'][1])
    agg_count += count_agg(sql['where'][::2])
    agg_count += count_agg(sql['groupBy'])
    if len(sql['orderBy']) > 0:
        agg_count += count_agg([unit[1] for unit in sql['orderBy'][1] if unit[1]] +
                            [unit[2] for unit in sql['orderBy'][1] if unit[2]])
    agg_count += count_agg(sql['having'])
    if agg_count > 1:
        count += 1

    # number of select columns
    if len(sql['select'][1]) > 1:
        count += 1

    # number of where conditions
    if len(sql['where']) > 1:
        count += 1

    # number of group by clauses
    if len(sql['groupBy']) > 1:
        count += 1

    return count


def eval_hardness(sql):
    count_comp1_ = count_component1(sql)
    count_comp2_ = count_component2(sql)
    count_others_ = count_others(sql)

    if count_comp1_ <= 1 and count_others_ == 0 and count_comp2_ == 0:
        return "easy"
    elif (count_others_ <= 2 and count_comp1_ <= 1 and count_comp2_ == 0) or \
            (count_comp1_ <= 2 and count_others_ < 2 and count_comp2_ == 0):
        return "medium"
    elif (count_others_ > 2 and count_comp1_ <= 2 and count_comp2_ == 0) or \
            (2 < count_comp1_ <= 3 and count_others_ <= 2 and count_comp2_ == 0) or \
            (count_comp1_ <= 1 and count_others_ == 0 and count_comp2_ <= 1):
        return "hard"
    else:
        return "extra"
