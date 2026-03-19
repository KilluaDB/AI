# -*- coding: utf-8 -*-
"""
PostgreSQL-adapted agents for text-to-SQL generation.
This module replaces SQLite-specific code with PostgreSQL-compatible queries.
"""
import os
import re
import sys
import json
import time
import logging
import psycopg2
from copy import deepcopy
from tqdm import trange
from typing import List, Dict, Any

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.propagate = False  # Prevent duplicate logging to root logger

# Create console handler with formatting
if not logger.handlers:
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('\033[0;36m[%(name)s]\033[0m %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

from core.const import (
    SELECTOR_NAME, DECOMPOSER_NAME, REFINER_NAME, SYSTEM_NAME,
    selector_template, decompose_template_bird, decompose_template_spider, refiner_template
)
from core.utils_pg import (
    extract_world_info, 
    is_email, 
    is_valid_date_column,
    parse_json, 
    parse_sql_from_string, 
    add_prefix
)
from func_timeout import func_set_timeout, FunctionTimedOut

INIT_LOG__PATH_FUNC = None
LLM_API_FUC = None
try:
    from core import api
    LLM_API_FUC = api.safe_call_llm
    INIT_LOG__PATH_FUNC = api.init_log_path
    print(f"Use func from core.api in agents_pg.py")
except:
    from core import llm
    LLM_API_FUC = llm.safe_call_llm
    INIT_LOG__PATH_FUNC = llm.init_log_path
    print(f"Use func from core.llm in agents_pg.py")


class BaseAgent:
    name = ""
    description = ""

    def __init__(self):
        pass

    def talk(self, message: dict):
        raise NotImplementedError


class Selector(BaseAgent):
    """
    Analyze database schema and prune irrelevant columns for focused SQL generation.
    Adapted for PostgreSQL databases.
    """
    name = SELECTOR_NAME
    description = "Analyze database schema and prune irrelevant tables/columns"

    def __init__(self, db_config: Dict[str, Any], schema_info: Dict[str, Any] = None, 
                 model_name: str = "gpt-4", dataset_name: str = "custom", 
                 lazy: bool = False, without_selector: bool = False):
        """
        Initialize Selector for PostgreSQL database.
        
        Args:
            db_config: PostgreSQL connection config {host, port, user, password, dbname}
            schema_info: Pre-extracted schema information (optional)
            model_name: LLM model name
            dataset_name: Dataset name for template selection
            lazy: If True, load schema info lazily
            without_selector: If True, skip pruning step
        """
        super().__init__()
        self.db_config = db_config
        self.model_name = model_name
        self.dataset_name = dataset_name
        self.without_selector = without_selector
        self._message = {}
        
        # Per-db_id schema cache: {db_id: {desc_dict, value_dict, pk_dict, fk_dict}}
        self._schema_cache = {}
        # Currently active db_id and its info
        self.db_info = {}
        self.schema_loaded = False
        self._current_schema = None
        
        if schema_info:
            self._load_schema_from_info(schema_info)
        elif not lazy:
            self._load_db_info()

    def _get_pg_connection(self, schema: str = None):
        """Get PostgreSQL connection, optionally setting search_path to *schema*."""
        conn = psycopg2.connect(
            host=self.db_config['host'],
            port=self.db_config['port'],
            user=self.db_config['user'],
            password=self.db_config['password'],
            dbname=self.db_config['dbname']
        )
        if schema:
            conn.autocommit = True
            cur = conn.cursor()
            cur.execute('SET search_path TO %s', (schema,))
            cur.close()
        return conn

    def _load_schema_from_info(self, schema_info: Dict[str, Any]):
        """Load schema from pre-extracted information."""
        self.db_info = {
            "desc_dict": {},
            "value_dict": {},
            "pk_dict": {},
            "fk_dict": {}
        }
        
        for table_name, columns in schema_info.items():
            self.db_info["desc_dict"][table_name] = []
            self.db_info["value_dict"][table_name] = []
            self.db_info["pk_dict"][table_name] = []
            self.db_info["fk_dict"][table_name] = []
            
            for col in columns:
                col_name = col['column_name']
                col_type = col.get('data_type', 'TEXT')
                is_nullable = col.get('is_nullable', 'YES')
                
                # desc_dict: [(column_name, full_column_name, extra_desc)]
                full_col_name = col_name.replace('_', ' ')
                self.db_info["desc_dict"][table_name].append([col_name, full_col_name, ''])
                
                # value_dict: [(column_name, value_examples_str)]
                self.db_info["value_dict"][table_name].append([col_name, ''])
                
        self.schema_loaded = True

    def _get_column_attributes(self, cursor, table_name: str, schema: str = 'public'):
        """
        Get column names and types from PostgreSQL using information_schema.
        Returns: (column_names_list, column_types_list)
        """
        query = """
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = %s AND table_schema = %s
            ORDER BY ordinal_position
        """
        cursor.execute(query, (table_name, schema))
        results = cursor.fetchall()
        
        column_names = [row[0] for row in results]
        column_types = [row[1].upper() for row in results]
        
        return column_names, column_types

    def _get_primary_keys(self, cursor, table_name: str, schema: str = 'public') -> List[str]:
        """Get primary key columns for a table."""
        query = """
            SELECT kcu.column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
                ON tc.constraint_name = kcu.constraint_name
                AND tc.table_schema = kcu.table_schema
            WHERE tc.constraint_type = 'PRIMARY KEY'
                AND tc.table_name = %s
                AND tc.table_schema = %s
        """
        cursor.execute(query, (table_name, schema))
        return [row[0] for row in cursor.fetchall()]

    def _get_foreign_keys(self, cursor, table_name: str, schema: str = 'public') -> List[tuple]:
        """
        Get foreign key relationships for a table.
        Returns: [(from_column, to_table, to_column), ...]
        """
        query = """
            SELECT
                kcu.column_name AS from_column,
                ccu.table_name AS to_table,
                ccu.column_name AS to_column
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
                ON tc.constraint_name = kcu.constraint_name
                AND tc.table_schema = kcu.table_schema
            JOIN information_schema.constraint_column_usage ccu
                ON tc.constraint_name = ccu.constraint_name
                AND tc.table_schema = ccu.table_schema
            WHERE tc.constraint_type = 'FOREIGN KEY'
                AND tc.table_name = %s
                AND tc.table_schema = %s
        """
        cursor.execute(query, (table_name, schema))
        return [(row[0], row[1], row[2]) for row in cursor.fetchall()]

    def _get_unique_column_values_str(self, cursor, table_name: str, 
                                       column_names: List[str], column_types: List[str],
                                       json_column_names: List[str], is_key_column_lst: List[bool]):
        """Get sample values for columns to help with query generation."""
        col_to_values_str_dict = {}
        col_to_values_str_lst = []

        for idx, column_name in enumerate(column_names):
            col_type = column_types[idx] if idx < len(column_types) else 'TEXT'
            lower_column_name = column_name.lower()
            
            # Skip sensitive or ID columns
            if lower_column_name.endswith('id') or \
               lower_column_name.endswith('email') or \
               lower_column_name.endswith('url'):
                col_to_values_str_dict[column_name] = ''
                continue

            try:
                # PostgreSQL uses double quotes for identifiers
                sql = f'SELECT "{column_name}" FROM "{table_name}" GROUP BY "{column_name}" ORDER BY COUNT(*) DESC LIMIT 10'
                cursor.execute(sql)
                values = cursor.fetchall()
                values = [value[0] for value in values]
                
                values_str = ''
                try:
                    values_str = self._get_value_examples_str(values, col_type)
                except Exception as e:
                    print(f"\nerror: get_value_examples_str failed, Exception:\n{e}\n")
                
                col_to_values_str_dict[column_name] = values_str
            except Exception as e:
                print(f"Error getting values for {table_name}.{column_name}: {e}")
                col_to_values_str_dict[column_name] = ''

        for k, column_name in enumerate(json_column_names):
            values_str = ''
            is_key = is_key_column_lst[k] if k < len(is_key_column_lst) else False

            if is_key:
                values_str = ''
            elif column_name in col_to_values_str_dict:
                values_str = col_to_values_str_dict[column_name]
            else:
                values_str = ''
            
            col_to_values_str_lst.append([column_name, values_str])
        
        return col_to_values_str_lst

    def _get_value_examples_str(self, values: List[object], col_type: str):
        """Format sample values as a string for prompts."""
        if not values:
            return ''
        
        # Map PostgreSQL types
        numeric_types = ['INTEGER', 'INT', 'BIGINT', 'SMALLINT', 'REAL', 'DOUBLE PRECISION', 
                        'NUMERIC', 'DECIMAL', 'SERIAL', 'BIGSERIAL']
        text_types = ['TEXT', 'VARCHAR', 'CHARACTER VARYING', 'CHAR', 'CHARACTER']
        
        if len(values) > 10 and col_type in numeric_types:
            return ''
        
        vals = []
        has_null = False
        for v in values:
            if v is None:
                has_null = True
            else:
                tmp_v = str(v).strip()
                if tmp_v != '':
                    vals.append(v)
        
        if not vals:
            return ''
        
        # Filter text values
        if col_type in text_types:
            new_values = []
            for v in vals:
                if not isinstance(v, str):
                    new_values.append(v)
                else:
                    v = v.strip()
                    if v == '':
                        continue
                    elif ('https://' in v) or ('http://' in v):
                        return ''
                    elif is_email(v):
                        return ''
                    else:
                        new_values.append(v)
            vals = new_values
            if not vals:
                return ''
            max_len = max(len(str(a)) for a in vals)
            if max_len > 50:
                return ''
        
        if not vals:
            return ''
        
        vals = vals[:6]
        
        if is_valid_date_column(vals):
            vals = vals[:1]
        
        if has_null:
            vals.insert(0, None)
        
        return str(vals)

    def _load_db_info(self, schema: str = 'public'):
        """Load database schema information from PostgreSQL for a specific schema."""
        print(f"\nLoading PostgreSQL schema '{schema}'...", flush=True)
        
        try:
            conn = self._get_pg_connection(schema=schema)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = %s AND table_type = 'BASE TABLE'
            """, (schema,))
            table_names = [row[0] for row in cursor.fetchall()]
            
            self.db_info = {
                "desc_dict": {},
                "value_dict": {},
                "pk_dict": {},
                "fk_dict": {}
            }
            
            for table_name in table_names:
                column_names, column_types = self._get_column_attributes(cursor, table_name, schema)
                pk_columns = self._get_primary_keys(cursor, table_name, schema)
                fk_list = self._get_foreign_keys(cursor, table_name, schema)
                
                # Build is_key_column_lst
                fk_columns = [fk[0] for fk in fk_list]
                is_key_column_lst = [col in pk_columns or col in fk_columns for col in column_names]
                
                # Get sample values
                col_values = self._get_unique_column_values_str(
                    cursor, table_name, column_names, column_types, 
                    column_names, is_key_column_lst
                )
                
                # Build desc_dict: [(column_name, full_column_name, extra_desc)]
                col_desc = []
                for col_name in column_names:
                    full_name = col_name.replace('_', ' ')
                    col_desc.append([col_name, full_name, ''])
                
                self.db_info["desc_dict"][table_name] = col_desc
                self.db_info["value_dict"][table_name] = col_values
                self.db_info["pk_dict"][table_name] = pk_columns
                self.db_info["fk_dict"][table_name] = fk_list
            
            cursor.close()
            conn.close()
            self._schema_cache[schema] = self.db_info
            self._current_schema = schema
            self.schema_loaded = True
            print(f"Loaded schema '{schema}': {len(table_names)} tables", flush=True)
            
        except Exception as e:
            print(f"Error loading database schema '{schema}': {e}", flush=True)
            raise

    def _build_table_schema_str(self, table_name: str, columns_desc: List, columns_val: List):
        """Build schema description string for a table."""
        schema_str = f"# Table: {table_name}\n"
        column_infos = []
        
        for (col_name, full_col_name, col_extra_desc), (_, col_values_str) in zip(columns_desc, columns_val):
            col_extra_desc = 'And ' + str(col_extra_desc) if col_extra_desc and str(col_extra_desc) != 'nan' else ''
            col_extra_desc = col_extra_desc[:100]
            
            col_line = f'  ({col_name},'
            if full_col_name:
                col_line += f" {full_col_name.strip()}."
            if col_values_str:
                col_line += f" Value examples: {col_values_str}."
            if col_extra_desc:
                col_line += f" {col_extra_desc}"
            col_line += '),'
            column_infos.append(col_line)
        
        schema_str += '[\n' + '\n'.join(column_infos).rstrip(',') + '\n]\n'
        return schema_str

    def _ensure_schema(self, db_id: str = None):
        """Load schema for *db_id* if not already cached. Falls back to 'public'."""
        schema = db_id or 'public'
        if schema in self._schema_cache:
            self.db_info = self._schema_cache[schema]
            self._current_schema = schema
            self.schema_loaded = True
        else:
            self._load_db_info(schema=schema)

    def _get_db_desc_str(self, extracted_schema: dict = None, use_gold_schema: bool = False):
        """
        Build database schema description for prompts.
        
        Args:
            extracted_schema: {table_name: "keep_all" or "drop_all" or ['col_a', 'col_b']}
        
        Returns:
            (schema_desc_str, fk_desc_str, chosen_schema_dict)
        """
        if not self.schema_loaded:
            self._load_db_info()
        
        extracted_schema = extracted_schema or {}
        
        desc_info = self.db_info['desc_dict']
        value_info = self.db_info['value_dict']
        pk_info = self.db_info['pk_dict']
        fk_info = self.db_info['fk_dict']
        
        schema_desc_str = ''
        db_fk_infos = []
        chosen_db_schema_dict = {}
        
        for table_name in desc_info.keys():
            columns_desc = desc_info[table_name]
            columns_val = value_info.get(table_name, [])
            pk_cols = pk_info.get(table_name, [])
            fk_list = fk_info.get(table_name, [])
            
            table_decision = extracted_schema.get(table_name, '')
            if table_decision == '' and use_gold_schema:
                continue
            
            all_columns = [name for name, _, _ in columns_desc]
            fk_columns = [fk[0] for fk in fk_list]
            important_keys = pk_cols + fk_columns
            
            new_columns_desc = []
            new_columns_val = []
            
            if table_decision == "drop_all":
                new_columns_desc = deepcopy(columns_desc[:6])
                new_columns_val = deepcopy(columns_val[:6]) if columns_val else [[c[0], ''] for c in new_columns_desc]
            elif table_decision == "keep_all" or table_decision == '':
                new_columns_desc = deepcopy(columns_desc)
                new_columns_val = deepcopy(columns_val) if columns_val else [[c[0], ''] for c in new_columns_desc]
            else:
                llm_chosen_columns = table_decision
                append_col_names = []
                for idx, col in enumerate(all_columns):
                    if col in important_keys or col in llm_chosen_columns:
                        new_columns_desc.append(columns_desc[idx])
                        if columns_val and idx < len(columns_val):
                            new_columns_val.append(columns_val[idx])
                        else:
                            new_columns_val.append([col, ''])
                        append_col_names.append(col)
                
                # Ensure at least 6 columns
                if len(all_columns) > 6 and len(new_columns_val) < 6:
                    for idx, col in enumerate(all_columns):
                        if len(append_col_names) >= 6:
                            break
                        if col not in append_col_names:
                            new_columns_desc.append(columns_desc[idx])
                            if columns_val and idx < len(columns_val):
                                new_columns_val.append(columns_val[idx])
                            else:
                                new_columns_val.append([col, ''])
                            append_col_names.append(col)
            
            chosen_db_schema_dict[table_name] = [col_name for col_name, _, _ in new_columns_desc]
            schema_desc_str += self._build_table_schema_str(table_name, new_columns_desc, new_columns_val)
            
            # Build foreign key descriptions
            for col_name, to_table, to_col in fk_list:
                fk_link_str = f'{table_name}."{col_name}" = {to_table}."{to_col}"'
                if fk_link_str not in db_fk_infos:
                    db_fk_infos.append(fk_link_str)
        
        fk_desc_str = '\n'.join(db_fk_infos)
        return schema_desc_str.strip(), fk_desc_str.strip(), chosen_db_schema_dict

    def _is_need_prune(self, db_schema: str):
        """Check if schema pruning is needed based on complexity."""
        total_columns = sum(len(cols) for cols in self.db_info['desc_dict'].values())
        avg_columns = total_columns / max(len(self.db_info['desc_dict']), 1)
        
        return not (avg_columns <= 6 and total_columns <= 30)

    def _prune(self, query: str, db_schema: str, db_fk: str, evidence: str = None) -> dict:
        """Use LLM to prune irrelevant schema elements."""
        db_id = self.db_config.get('dbname', 'database')
        prompt = selector_template.format(
            db_id=db_id, query=query, evidence=evidence, 
            desc_str=db_schema, fk_str=db_fk
        )
        word_info = extract_world_info(self._message)
        reply = LLM_API_FUC(prompt, **word_info)
        return parse_json(reply)

    def talk(self, message: dict):
        """
        Process message and extract relevant schema.
        
        Args:
            message: {
                "db_id": database identifier (used as PG schema name),
                "query": user_query,
                "evidence": extra_info,
                "extracted_schema": pre-extracted schema (optional)
            }
        """
        if message['send_to'] != self.name:
            return
        
        logger.info("="*60)
        logger.info(f"\033[1;33m[SELECTOR] Starting schema extraction\033[0m")
        logger.info(f"Query: {message.get('query', '')[:100]}...")
        
        db_id = message.get('db_id')
        self._ensure_schema(db_id)
        
        self._message = message
        ext_sch = message.get('extracted_schema', {})
        query = message.get('query')
        evidence = message.get('evidence', '')
        
        use_gold_schema = bool(ext_sch)
        db_schema, db_fk, chosen_db_schema_dict = self._get_db_desc_str(
            extracted_schema=ext_sch, use_gold_schema=use_gold_schema
        )
        
        logger.debug(f"Initial schema tables: {list(chosen_db_schema_dict.keys())}")
        
        need_prune = self._is_need_prune(db_schema)
        if self.without_selector:
            need_prune = False
        
        logger.info(f"Schema pruning needed: {need_prune}")
        
        if ext_sch == {} and need_prune:
            try:
                logger.info("Calling LLM for schema pruning...")
                raw_extracted_schema = self._prune(
                    query=query, db_schema=db_schema, db_fk=db_fk, evidence=evidence
                )
                logger.info(f"Pruned schema: {raw_extracted_schema}")
            except Exception as e:
                logger.error(f"Pruning failed: {e}")
                raw_extracted_schema = {}
            
            db_schema, db_fk, chosen_db_schema_dict = self._get_db_desc_str(
                extracted_schema=raw_extracted_schema
            )
            
            message['extracted_schema'] = raw_extracted_schema
            message['chosen_db_schem_dict'] = chosen_db_schema_dict
            message['desc_str'] = db_schema
            message['fk_str'] = db_fk
            message['pruned'] = True
        else:
            message['chosen_db_schem_dict'] = chosen_db_schema_dict
            message['desc_str'] = db_schema
            message['fk_str'] = db_fk
            message['pruned'] = False
        
        logger.info(f"\033[1;32m[SELECTOR OUTPUT]\033[0m")
        logger.info(f"Tables selected: {list(chosen_db_schema_dict.keys())}")
        logger.info(f"Schema pruned: {message['pruned']}")
        logger.debug(f"Schema description (first 500 chars):\n{db_schema[:500]}...")
        logger.info(f"Forwarding to: {DECOMPOSER_NAME}")
        logger.info("="*60)
        
        message['send_to'] = DECOMPOSER_NAME


class Decomposer(BaseAgent):
    """Decompose the question and solve using Chain-of-Thought."""
    name = DECOMPOSER_NAME
    description = "Decompose the question and generate SQL using CoT"

    def __init__(self, dataset_name: str = "custom"):
        super().__init__()
        self.dataset_name = dataset_name
        self._message = {}

    def talk(self, message: dict):
        """
        Process message and generate SQL.
        
        Args:
            message: {
                "query": user_query,
                "evidence": extra_info,
                "desc_str": schema description,
                "fk_str": foreign key info
            }
        """
        if message['send_to'] != self.name:
            return
        
        logger.info("="*60)
        logger.info(f"\033[1;33m[DECOMPOSER] Starting SQL generation\033[0m")
        logger.info(f"Query: {message.get('query', '')[:100]}...")
        
        self._message = message
        query = message.get('query')
        evidence = message.get('evidence', '')
        schema_info = message.get('desc_str')
        fk_info = message.get('fk_str')
        
        logger.debug(f"Evidence: {evidence[:200] if evidence else 'None'}")
        logger.debug(f"Using template: {'bird' if self.dataset_name == 'bird' else 'spider/custom'}")
        
        # Select template based on dataset
        if self.dataset_name == 'bird':
            prompt = decompose_template_bird.format(
                query=query, desc_str=schema_info, fk_str=fk_info, evidence=evidence
            )
        else:
            prompt = decompose_template_spider.format(
                query=query, desc_str=schema_info, fk_str=fk_info
            )
        
        logger.info("Calling LLM for SQL generation...")
        logger.debug(f"Prompt length: {len(prompt)} chars")
        
        word_info = extract_world_info(self._message)
        reply = LLM_API_FUC(prompt, **word_info).strip()
        
        logger.info(f"\033[1;32m[DECOMPOSER LLM RESPONSE]\033[0m")
        logger.info(f"Response length: {len(reply)} chars")
        logger.debug(f"Full response:\n{reply}")
        
        qa_pairs = reply
        try:
            res = parse_sql_from_string(reply)
            logger.info(f"Parsed SQL successfully")
        except Exception as e:
            res = f'error: {str(e)}'
            logger.error(f"Failed to parse SQL: {e}")
        
        message['final_sql'] = res
        message['qa_pairs'] = qa_pairs
        message['fixed'] = False
        
        logger.info(f"\033[1;32m[DECOMPOSER OUTPUT]\033[0m")
        logger.info(f"Generated SQL: {res}")
        logger.info(f"Forwarding to: {REFINER_NAME}")
        logger.info("="*60)
        
        message['send_to'] = REFINER_NAME


class Refiner(BaseAgent):
    """Execute SQL and perform validation/refinement."""
    name = REFINER_NAME
    description = "Execute SQL and refine based on errors"

    def __init__(self, db_config: Dict[str, Any], dataset_name: str = "custom"):
        """
        Initialize Refiner.
        
        Args:
            db_config: PostgreSQL connection config
            dataset_name: Dataset name for validation rules
        """
        super().__init__()
        self.db_config = db_config
        self.dataset_name = dataset_name
        self._message = {}
        self._current_schema = None

    def _get_pg_connection(self, schema: str = None):
        """Get PostgreSQL connection, optionally setting search_path."""
        conn = psycopg2.connect(
            host=self.db_config['host'],
            port=self.db_config['port'],
            user=self.db_config['user'],
            password=self.db_config['password'],
            dbname=self.db_config['dbname']
        )
        if schema:
            conn.autocommit = True
            cur = conn.cursor()
            cur.execute('SET search_path TO %s', (schema,))
            cur.close()
        return conn

    @func_set_timeout(120)
    def _execute_sql(self, sql: str) -> dict:
        """Execute SQL on PostgreSQL and return results."""
        try:
            conn = self._get_pg_connection(schema=self._current_schema)
            cursor = conn.cursor()
            cursor.execute(sql)
            result = cursor.fetchall()
            cursor.close()
            conn.close()
            return {
                "sql": str(sql),
                "data": result[:5],
                "pg_error": "",
                "exception_class": ""
            }
        except psycopg2.Error as er:
            return {
                "sql": str(sql),
                "pg_error": str(er.pgerror) if er.pgerror else str(er),
                "exception_class": str(er.__class__.__name__)
            }
        except Exception as e:
            return {
                "sql": str(sql),
                "pg_error": str(e),
                "exception_class": str(type(e).__name__)
            }

    def _extract_identifiers_from_sql(self, sql: str) -> set:
        """Extract quoted and unquoted identifiers used in SQL."""
        identifiers = set()
        for m in re.finditer(r'"([^"]+)"', sql):
            identifiers.add(m.group(1).lower())
        for kw in ('SELECT', 'FROM', 'JOIN', 'WHERE', 'GROUP', 'ORDER',
                    'HAVING', 'ON', 'AND', 'OR', 'AS', 'BY', 'NOT',
                    'NULL', 'IS', 'IN', 'BETWEEN', 'LIKE', 'INNER',
                    'LEFT', 'RIGHT', 'OUTER', 'CROSS', 'DISTINCT',
                    'COUNT', 'SUM', 'AVG', 'MAX', 'MIN', 'CAST',
                    'REAL', 'INTEGER', 'TEXT', 'NULLIF', 'COALESCE',
                    'CASE', 'WHEN', 'THEN', 'ELSE', 'END', 'DESC',
                    'ASC', 'LIMIT', 'OFFSET', 'OVER', 'PARTITION',
                    'RANK', 'ROW_NUMBER', 'DENSE_RANK', 'WITH',
                    'UNION', 'ALL', 'EXISTS', 'TRUE', 'FALSE',
                    'TIMESTAMP', 'TO_CHAR', 'EXTRACT'):
            pass  # just defining the set below
        return identifiers

    def _check_columns_exist(self, sql: str, schema_desc: str) -> str:
        """
        Validate that quoted identifiers in *sql* actually appear in
        *schema_desc* (the schema string shown to the LLM).
        Returns an error message for the first mismatch, or '' if all ok.
        """
        if not schema_desc:
            return ''
        schema_lower = schema_desc.lower()
        for m in re.finditer(r'"([^"]+)"', sql):
            ident = m.group(1)
            if ident.lower() in ('real', 'integer', 'text', 'timestamp',
                                  'date', 'boolean', 'numeric', 'float',
                                  'varchar', 'bigint', 'smallint',
                                  'average_score'):
                continue
            if ident.lower() not in schema_lower:
                return (f'Column or table "{ident}" does not exist in the '
                        f'database schema. Check the schema and use only '
                        f'columns that appear there.')
        return ''

    def _is_need_refine(self, exec_result: dict) -> bool:
        """Check if SQL needs refinement based on execution result."""
        if self.dataset_name == 'spider':
            return 'data' not in exec_result
        
        data = exec_result.get('data')
        if data is not None:
            if len(data) == 0:
                exec_result['pg_error'] = 'no data selected'
                return True
            for t in data:
                for n in t:
                    if n is None:
                        exec_result['pg_error'] = 'exist None value, consider adding NOT NULL filter'
                        return True
            return False
        return True

    def _refine(self, query: str, evidence: str, schema_info: str, 
                fk_info: str, error_info: dict) -> str:
        """Use LLM to refine SQL based on error."""
        sql_arg = add_prefix(error_info.get('sql'))
        pg_error = error_info.get('pg_error', error_info.get('sqlite_error', ''))
        exception_class = error_info.get('exception_class')
        
        prompt = refiner_template.format(
            query=query, evidence=evidence, desc_str=schema_info,
            fk_str=fk_info, sql=sql_arg, pg_error=pg_error,
            exception_class=exception_class
        )
        
        word_info = extract_world_info(self._message)
        reply = LLM_API_FUC(prompt, **word_info)
        return parse_sql_from_string(reply)

    def talk(self, message: dict):
        """
        Execute and validate/refine SQL.
        
        Args:
            message: {
                "query": user_query,
                "evidence": extra_info,
                "desc_str": schema description,
                "fk_str": foreign key info,
                "final_sql": SQL to validate,
                "db_id": database name (used as PG schema)
            }
        """
        if message['send_to'] != self.name:
            return
        
        logger.info("="*60)
        logger.info(f"\033[1;33m[REFINER] Starting SQL validation\033[0m")
        
        self._current_schema = message.get('db_id')
        self._message = message
        old_sql = message.get('pred', message.get('final_sql'))
        query = message.get('query')
        evidence = message.get('evidence', '')
        schema_info = message.get('desc_str')
        fk_info = message.get('fk_str')
        
        try_times = message.get('try_times', 0)
        logger.info(f"Attempt #{try_times + 1}")
        logger.info(f"SQL to validate: {old_sql}")
        
        # Don't fix SQL containing "error" string
        if 'error' in old_sql.lower():
            logger.warning(f"SQL contains error, skipping refinement")
            message['try_times'] = message.get('try_times', 0) + 1
            message['pred'] = old_sql
            message['send_to'] = SYSTEM_NAME
            logger.info(f"\033[1;31m[REFINER] Terminated - Error in SQL\033[0m")
            return
        
        is_timeout = False
        error_info = {}
        try:
            logger.info(f"Executing SQL on PostgreSQL...")
            error_info = self._execute_sql(old_sql)
            logger.info(f"\033[1;32m[REFINER EXECUTION RESULT]\033[0m")
            if error_info.get('data') is not None:
                logger.info(f"Execution successful! Rows returned: {len(error_info.get('data', []))}")
                logger.debug(f"Sample data: {error_info.get('data', [])[:3]}")
            else:
                logger.warning(f"Execution error: {error_info.get('pg_error', 'Unknown')}")
        except FunctionTimedOut:
            is_timeout = True
            logger.warning(f"SQL execution timed out (>120s)")
        except Exception as e:
            is_timeout = True
            logger.error(f"SQL execution error: {e}")
        
        is_need = self._is_need_refine(error_info) if error_info else True
        
        if not is_need and schema_info:
            col_err = self._check_columns_exist(old_sql, schema_info)
            if col_err:
                logger.warning(f"Column mismatch detected: {col_err}")
                is_need = True
                error_info['pg_error'] = col_err
                error_info['exception_class'] = 'ColumnNotFound'
        
        logger.info(f"Needs refinement: {is_need}, Timeout: {is_timeout}")
        
        if not is_need or is_timeout:
            # Correct on first pass, or timeout
            message['try_times'] = message.get('try_times', 0) + 1
            message['pred'] = old_sql
            message['send_to'] = SYSTEM_NAME
            logger.info(f"\033[1;32m[REFINER OUTPUT]\033[0m")
            logger.info(f"Final SQL (no refinement needed): {old_sql}")
            logger.info(f"Forwarding to: {SYSTEM_NAME} (DONE)")
        else:
            # Refine SQL
            logger.info(f"Calling LLM for SQL refinement...")
            logger.info(f"Error to fix: {error_info.get('pg_error', 'Unknown')}")
            try:
                new_sql = self._refine(query, evidence, schema_info, fk_info, error_info)
                logger.info(f"Refinement successful")
            except Exception as e:
                logger.error(f"Refinement failed: {e}")
                new_sql = old_sql
            
            message['try_times'] = message.get('try_times', 0) + 1
            message['pred'] = new_sql
            message['fixed'] = True
            message['send_to'] = REFINER_NAME
            
            logger.info(f"\033[1;32m[REFINER OUTPUT]\033[0m")
            logger.info(f"Refined SQL: {new_sql}")
            logger.info(f"Forwarding to: {REFINER_NAME} (retry)")
        
        logger.info("="*60)
