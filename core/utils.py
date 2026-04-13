# -*- coding: utf-8 -*-
import os
import re
import random
import json
import time
import psycopg2
from core.const import subq_pattern
from typing import Dict, List, Any, Optional


def is_valid_date(date_str):
    if (not isinstance(date_str, str)):
        return False
    date_str = date_str.split()[0]
    if len(date_str) != 10:
        return False
    pattern = r'^\d{4}-\d{2}-\d{2}$'
    if re.match(pattern, date_str):
        year, month, day = map(int, date_str.split('-'))
        if year < 1 or month < 1 or month > 12 or day < 1 or day > 31:
            return False
        else:
            return True
    else:
        return False


def is_valid_date_column(col_value_lst):
    for col_value in col_value_lst:
        if not is_valid_date(col_value):
            return False
    return True


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


def is_email(string):
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    match = re.match(pattern, string)
    if match:
        return True
    else:
        return False



def extract_world_info(message_dict: dict):
    info_dict = {}
    info_dict['idx'] = message_dict['idx']
    info_dict['db_id'] = message_dict['db_id']
    info_dict['query'] = message_dict['query']
    info_dict['evidence'] = message_dict.get('evidence', '')
    info_dict['difficulty'] = message_dict.get('difficulty', '')
    info_dict['ground_truth'] = message_dict.get('ground_truth', '')
    info_dict['send_to'] = message_dict.get('send_to', '')
    return info_dict


def replace_multiple_spaces(text):
    # 定义正则表达式，匹配多个空字符
    pattern = r'\s+'
    # 将多个空字符替换成一个空格
    new_text = re.sub(pattern, ' ', text)
    return new_text


# SQL parsing
def extract_table_names(sql_query):
    sql_query = sql_query.replace('`', '').replace('"', '')
    table_names = re.findall(r'FROM\s+([\w]+)', sql_query, re.IGNORECASE) + \
                  re.findall(r'JOIN\s+([\w]+)', sql_query, re.IGNORECASE)
    return set(table_names)


def _get_pg_conn(schema: str = "public"):
    """Return a PostgreSQL connection. PG_DSN env must be set. Sets search_path to schema."""
    dsn = os.environ.get("PG_DSN")
    if not dsn:
        raise RuntimeError("PG_DSN environment variable is not set for PostgreSQL connection")
    conn = psycopg2.connect(dsn)
    with conn.cursor() as cur:
        cur.execute("SET search_path TO %s", (schema,))
    return conn


def get_used_tables(sql: str, db_config: Any = None, schema: str = "public") -> dict:
    """db_config: optional dict or DSN string; None = use PG_DSN. schema: schema name (db_id). If db_config is a path string (e.g. .../db_id/db_id.sqlite), it is treated as schema = db_id."""
    if isinstance(db_config, str) and (".sqlite" in db_config or "/" in db_config or "\\" in db_config):
        schema = os.path.basename(db_config.rstrip("/\\")).replace(".sqlite", "") or schema
        db_config = None
    table_names = extract_table_names(sql)
    sch = {}
    if db_config is None:
        conn = _get_pg_conn(schema=schema)
    else:
        conn = psycopg2.connect(**db_config) if isinstance(db_config, dict) else psycopg2.connect(db_config)
        if schema and schema != "public":
            with conn.cursor() as cur:
                cur.execute("SET search_path TO %s", (schema,))
    cursor = conn.cursor()
    for table_name in table_names:
        cursor.execute("""
            SELECT column_name FROM information_schema.columns
            WHERE table_schema = %s AND table_name = %s ORDER BY ordinal_position
        """, (schema, table_name))
        columns = cursor.fetchall()
        column_names = [c[0] for c in columns]
        sch[table_name] = {"chosen columns": column_names, "discarded columns": []}
    cursor.close()
    conn.close()
    return sch


def get_all_tables(db_config: Any = None, schema: str = "public") -> dict:
    """db_config: optional; if None use PG_DSN. schema: schema name (db_id). If db_config is a path string, schema is derived from it."""
    if isinstance(db_config, str) and (".sqlite" in db_config or "/" in db_config or "\\" in db_config):
        schema = os.path.basename(db_config.rstrip("/\\")).replace(".sqlite", "") or schema
        db_config = None
    if db_config is None:
        conn = _get_pg_conn(schema=schema)
    else:
        conn = psycopg2.connect(**db_config) if isinstance(db_config, dict) else psycopg2.connect(db_config)
        if schema and schema != "public":
            with conn.cursor() as cur:
                cur.execute("SET search_path TO %s", (schema,))
    cursor = conn.cursor()
    cursor.execute("""
        SELECT table_name FROM information_schema.tables
        WHERE table_schema = %s AND table_type = 'BASE TABLE'
    """, (schema,))
    table_names = [r[0] for r in cursor.fetchall()]
    sch = {}
    for table_name in table_names:
        cursor.execute("""
            SELECT column_name FROM information_schema.columns
            WHERE table_schema = %s AND table_name = %s ORDER BY ordinal_position
        """, (schema, table_name))
        columns = cursor.fetchall()
        column_names = [c[0] for c in columns]
        sch[table_name] = {"chosen columns": column_names, "discarded columns": []}
    cursor.close()
    conn.close()
    return sch


gold_schema = []


def get_gold_columns(idx: int, db_config: Any = None, schema: str = "public") -> dict:
    """db_config: optional; if None use PG_DSN. schema: schema name (db_id). If db_config is a path string, schema is derived from it."""
    if isinstance(db_config, str) and (".sqlite" in db_config or "/" in db_config or "\\" in db_config):
        schema = os.path.basename(db_config.rstrip("/\\")).replace(".sqlite", "") or schema
        db_config = None
    global gold_schema
    if gold_schema == []:
        input_file = "data/bird/dev_gold_schema.json"
        with open(input_file, encoding='utf8') as f:
            gold_schema = json.load(f)
    table2cols = gold_schema[idx]["columns_map"]

    if db_config is None:
        conn = _get_pg_conn(schema=schema)
    else:
        conn = psycopg2.connect(**db_config) if isinstance(db_config, dict) else psycopg2.connect(db_config)
        if schema and schema != "public":
            with conn.cursor() as cur:
                cur.execute("SET search_path TO %s", (schema,))
    cursor = conn.cursor()
    cursor.execute("""
        SELECT table_name FROM information_schema.tables
        WHERE table_schema = %s AND table_type = 'BASE TABLE'
    """, (schema,))
    table_names = [r[0] for r in cursor.fetchall()]
    sch = {}
    for table_name in table_names:
        cursor.execute("""
            SELECT column_name FROM information_schema.columns
            WHERE table_schema = %s AND table_name = %s ORDER BY ordinal_position
        """, (schema, table_name))
        columns = cursor.fetchall()
        all_columns = [c[0] for c in columns]
        gold_columns = table2cols.get(table_name, [])
        gold_columns = [str(item).replace('`', '').replace('"', '') for item in gold_columns]
        unused_columns = list(set(all_columns).difference(set(gold_columns)))
        random.shuffle(unused_columns)
        sch[table_name] = {
            "chosen columns": gold_columns + unused_columns[:3],
            "discarded columns": []
        }
    cursor.close()
    conn.close()
    return sch


# GPT result parsing


# def parse_json(res: str) -> dict:
#     lines = res.split('\n')
#     start_idx, end_idx = -1, -1
#     for idx in range(0, len(lines)):
#         if '```json' in lines[idx]:
#             start_idx = idx
#             break
#     if start_idx == -1: return {}
#     for idx in range(start_idx + 1, len(lines)):
#         if '```' in lines[idx]:
#             end_idx = idx
#             break
#     if end_idx == -1: return {}
#     jstr = " ".join(lines[start_idx + 1: end_idx])
#     return json.loads(jstr)


# parse json output
def parse_json(text: str) -> dict:
    # Try parse JSON inside markdown block first
    block_match = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL | re.IGNORECASE)
    candidates = []
    if block_match:
        candidates.append(block_match.group(1).strip())

    # Also try full text (some models return plain JSON without fences)
    candidates.append(text.strip())

    for json_string in candidates:
        if not json_string:
            continue
        try:
            json_data = json.loads(json_string)
            if isinstance(json_data, dict) and check_selector_response(json_data):
                return json_data
        except Exception:
            continue

    # Last attempt: extract first {...} region and parse it
    brace_match = re.search(r"\{.*\}", text, re.DOTALL)
    if brace_match:
        try:
            json_data = json.loads(brace_match.group(0))
            if isinstance(json_data, dict) and check_selector_response(json_data):
                return json_data
        except Exception:
            pass

    return {}


# check if valid format
def check_selector_response(json_data: Dict) -> bool:
    FLAGS = ['keep_all', 'drop_all']
    # Sometimes model returns {"query": "SELECT ..."}; not a selector schema map.
    # Treat as invalid silently (no noisy logs).
    if isinstance(json_data, dict) and set(json_data.keys()) == {'query'}:
        return False

    for k, v in json_data.items():
        if isinstance(v, str):
            if v not in FLAGS:
                print(f"error: invalid table flag: {v}\n")
                print(f"json_data: {json_data}\n\n")
                return False
        elif isinstance(v, list):
            pass
        else:
            print(f"error: invalid flag type: {v}\n")
            print(f"json_data: {json_data}\n\n")
            return False
    return True


def get_files(root, suffix):
    """
    获取指定目录下的所有指定后缀的文件
    :param root: 指定目录 str 类型  如：'.'
    :param suffix: 指定后缀 str 类型 如：'.txt'
    :return: 文件列表 
    """
    import os
    import glob
    if not os.path.exists(root):
        raise FileNotFoundError(f'path {root} not found.')
    res = glob.glob(f'{root}/**/*{suffix}', recursive=True)
    res = [os.path.abspath(p) for p in res]
    return res


# read txt file to string list and strip empty lines
def read_txt_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        print(f"load txt file from {path}")
        return [line.strip() for line in f if line.strip()!= '']

def load_json_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        print(f"load json file from {path}")
        return json.load(f)


def load_jsonl_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        data = []
        for line in f:
            js_str = line.strip()
            if js_str == '':
                continue
            js = json.loads(js_str)
            data.append(js)
        print(f"load jsonl file from {path}")
        return data


def append_file(path, string_lst):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'a+', encoding='utf-8') as f:
        for string in string_lst:
            if string[-1] != '\n':
                string += '\n'
            f.write(string)


def save_file(path, string_lst):
    """
    保存文件
    :param path: 文件路径 str 类型
    :param string_lst: 字符串列表, 带有换行符
    """
    with open(path, 'w', encoding='utf-8') as f:
        f.writelines(string_lst)
        print(f"save file to {path}")


def save_json_file(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"save json file to {path}")


def save_jsonl_file(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        for js in data:
            f.write(json.dumps(js, ensure_ascii=False) + '\n')
        print(f"save jsonl file to {path}")


# NOTE: parse_json is defined earlier in this file.


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


def parse_sql_from_string(input_string):
    if not input_string or not input_string.strip():
        return "error: No SQL found in the input string"

    text = input_string.strip()

    # 1) Prefer SQL fenced blocks
    sql_blocks = re.findall(r"```(?:sql)?\s*(.*?)\s*```", text, re.DOTALL | re.IGNORECASE)
    if sql_blocks:
        sql = sql_blocks[-1].strip()
        if sql:
            return re.sub(r"\s+", " ", sql).strip()

    # 2) Remove markdown artifacts / comments and normalize
    cleaned = text
    cleaned = re.sub(r"```(?:sql)?", "", cleaned, flags=re.IGNORECASE)
    cleaned = cleaned.replace("```", "")
    cleaned = re.sub(r"--[^\n]*", "", cleaned)
    cleaned = re.sub(r"/\*.*?\*/", "", cleaned, flags=re.DOTALL)
    cleaned = cleaned.strip()

    # 3) If model returned raw SQL (common with strict prompts), accept it
    if re.match(r"(?is)^\s*(with|select)\b", cleaned):
        return re.sub(r"\s+", " ", cleaned).strip()

    # 4) Extract first WITH/SELECT statement from mixed text
    match = re.search(r"(?is)((?:with\b.*?\bselect\b.*?|select\b.*?))(?:;|$)", cleaned)
    if match:
        sql = match.group(1).strip()
        if sql:
            return re.sub(r"\s+", " ", sql).strip()

    return "error: No SQL found in the input string"


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
