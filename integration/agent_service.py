"""
Agent Service - Integrates the existing multi-agent system (Decomposer, Selector, Refiner)
with FastAPI for text-to-SQL generation.
"""

import sys
import os
import json
import tempfile
import logging

# Add project root to path to import core modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import psycopg2

logger = logging.getLogger(__name__)


class AgentService:
    """
    Wraps the existing multi-agent ChatManager to provide text-to-SQL capabilities.
    
    Pipeline: Selector → Decomposer → Refiner
    - Selector: Extracts relevant schema elements
    - Decomposer: Breaks complex questions into sub-questions
    - Refiner: Validates and fixes generated SQL
    """
    
    def __init__(self, api_key: str = None, model_name: str = None, api_base: str = None):
        """
        Initialize the agent service with LLM configuration.
        
        If parameters are not provided, falls back to values from api_config.py
        """
        from core import api_config
        
        # Use provided values or fall back to api_config defaults
        self.api_key = api_key or api_config.OPENAI_API_KEY
        self.model_name = model_name or api_config.MODEL_NAME
        self.api_base = api_base or api_config.OPENAI_API_BASE
        
        self._configure_llm()
        
    def _configure_llm(self):
        """Configure the LLM API settings"""
        from core import api_config
        api_config.MODEL_NAME = self.model_name
        api_config.openai.api_key = self.api_key
        api_config.openai.api_base = self.api_base
        api_config.openai.api_type = "open_ai"
        logger.info(f"LLM configured: model={self.model_name}, api_base={self.api_base}")

    def get_schema_from_db(self, db_config: dict) -> dict:
        """
        Extract schema from user's PostgreSQL database.
        Returns schema in the format expected by the agents.
        """
        schema = {
            "db_id": db_config.get("database", "user_db"),
            "table_names_original": [],
            "table_names": [],  # lowercase versions
            "column_names_original": [[-1, "*"]],
            "column_names": [[-1, "*"]],
            "column_types": ["text"],
            "foreign_keys": [],
            "primary_keys": []
        }
        
        try:
            conn = psycopg2.connect(
                host=db_config["host"],
                port=db_config["port"],
                dbname=db_config["database"],
                user=db_config["user"],
                password=db_config["password"]
            )
            cursor = conn.cursor()
            
            # Get all tables
            cursor.execute("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
            """)
            tables = [row[0] for row in cursor.fetchall()]
            schema["table_names_original"] = tables
            schema["table_names"] = [t.lower() for t in tables]
            
            # Get columns for each table
            for idx, table in enumerate(tables):
                cursor.execute("""
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_schema = 'public' AND table_name = %s
                    ORDER BY ordinal_position
                """, (table,))
                for col_name, col_type in cursor.fetchall():
                    schema["column_names_original"].append([idx, col_name])
                    schema["column_names"].append([idx, col_name.lower()])
                    schema["column_types"].append(col_type)
            
            # Get primary keys
            cursor.execute("""
                SELECT tc.table_name, kcu.column_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu 
                    ON tc.constraint_name = kcu.constraint_name
                    AND tc.table_schema = kcu.table_schema
                WHERE tc.constraint_type = 'PRIMARY KEY' 
                    AND tc.table_schema = 'public'
            """)
            for table_name, col_name in cursor.fetchall():
                if table_name in tables:
                    table_idx = tables.index(table_name)
                    for col_idx, (tbl_idx, c_name) in enumerate(schema["column_names_original"]):
                        if tbl_idx == table_idx and c_name == col_name:
                            schema["primary_keys"].append(col_idx)
            
            # Get foreign keys
            cursor.execute("""
                SELECT
                    kcu.table_name, kcu.column_name,
                    ccu.table_name AS foreign_table, ccu.column_name AS foreign_column
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu
                    ON tc.constraint_name = kcu.constraint_name
                    AND tc.table_schema = kcu.table_schema
                JOIN information_schema.constraint_column_usage ccu
                    ON ccu.constraint_name = tc.constraint_name
                    AND ccu.table_schema = tc.table_schema
                WHERE tc.constraint_type = 'FOREIGN KEY'
                    AND tc.table_schema = 'public'
            """)
            for src_table, src_col, dst_table, dst_col in cursor.fetchall():
                if src_table in tables and dst_table in tables:
                    src_table_idx = tables.index(src_table)
                    dst_table_idx = tables.index(dst_table)
                    src_col_idx = None
                    dst_col_idx = None
                    for col_idx, (tbl_idx, c_name) in enumerate(schema["column_names_original"]):
                        if tbl_idx == src_table_idx and c_name == src_col:
                            src_col_idx = col_idx
                        if tbl_idx == dst_table_idx and c_name == dst_col:
                            dst_col_idx = col_idx
                    if src_col_idx and dst_col_idx:
                        schema["foreign_keys"].append([src_col_idx, dst_col_idx])
            
            conn.close()
            logger.info(f"Extracted schema: {len(tables)} tables")
            return schema
            
        except Exception as e:
            logger.error(f"Failed to extract schema: {e}")
            raise

    def generate_sql_with_agents(self, question: str, db_config: dict, hint: str = "") -> dict:
        """
        Generate SQL using the full multi-agent pipeline (PostgreSQL version).
        
        Pipeline:
        1. Selector - Identifies relevant tables and columns
        2. Decomposer - Breaks down complex questions
        3. Refiner - Validates and fixes SQL
        
        Returns:
            dict with keys: success, sql, error, tables_used
        """
        from core.chat_manager_pg import generate_sql_with_agents as pg_generate_sql
        from core.utils_pg import get_schema_info
        
        try:
            # Build db_config for PostgreSQL connection
            pg_config = {
                'host': db_config.get('host', 'localhost'),
                'port': db_config.get('port', 5432),
                'user': db_config.get('user', 'postgres'),
                'password': db_config.get('password', ''),
                'dbname': db_config.get('database', 'postgres')
            }
            
            # Get schema info
            schema_info = get_schema_info(pg_config)
            
            if not schema_info:
                return {
                    "success": False,
                    "error": "No tables found in database",
                    "sql": None,
                    "tables_used": []
                }
            
            # Use the new PostgreSQL multi-agent system
            logger.info(f"Starting PostgreSQL agent pipeline for: {question[:100]}...")
            
            result = pg_generate_sql(
                query=question,
                db_config=pg_config,
                schema_info=schema_info,
                evidence=hint,
                model_name=self.model_name,
                dataset_name="custom",
                without_selector=False
            )
            
            if result['success'] and result['sql']:
                logger.info(f"Generated SQL: {result['sql'][:200]}...")
                return {
                    "success": True,
                    "sql": result['sql'],
                    "error": None,
                    "tables_used": list(schema_info.keys()),
                    "pruned": result.get('pruned', False),
                    "fixed": result.get('fixed', False)
                }
            else:
                return {
                    "success": False,
                    "error": result.get('error', 'Agents failed to generate SQL'),
                    "sql": result.get('sql'),
                    "tables_used": list(schema_info.keys())
                }
                
        except Exception as e:
            logger.error(f"Agent pipeline failed: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e),
                "sql": None,
                "tables_used": []
            }

    def generate_sql_simple(self, question: str, db_config: dict, hint: str = "") -> dict:
        """
        Generate SQL using a simple single-LLM-call approach.
        Faster but less sophisticated than the multi-agent pipeline.
        
        Use this for simple queries or when speed is more important than accuracy.
        """
        from core.llm import safe_call_llm
        from core.utils_pg import parse_sql_from_string, get_schema_info, format_schema_for_prompt
        
        try:
            # Build db_config for PostgreSQL connection
            pg_config = {
                'host': db_config.get('host', 'localhost'),
                'port': db_config.get('port', 5432),
                'user': db_config.get('user', 'postgres'),
                'password': db_config.get('password', ''),
                'dbname': db_config.get('database', 'postgres')
            }
            
            # Get schema
            schema_info = get_schema_info(pg_config)
            
            if not schema_info:
                return {
                    "success": False,
                    "error": "No tables found in database",
                    "sql": None,
                    "tables_used": []
                }
            
            # Format schema for prompt
            schema_str = format_schema_for_prompt(schema_info)
            
            # Build prompt
            prompt = f"""You are a PostgreSQL expert. Given the database schema below, write a SQL query to answer the user's question.

### Database Schema:
{schema_str}

### User Question:
{question}

{f"### Hint: {hint}" if hint else ""}

### Instructions:
- Write ONLY the SQL query, nothing else
- Use PostgreSQL syntax
- Only use SELECT statements (no INSERT, UPDATE, DELETE, DROP, etc.)
- Use table and column names exactly as shown in the schema
- Wrap the SQL in ```sql and ``` markers

### SQL Query:
"""
            
            # Call LLM
            response = safe_call_llm(prompt)
            sql = parse_sql_from_string(response)
            generated_sql = sql if sql and 'error' not in sql.lower() else response.strip()
            
            return {
                "success": True,
                "sql": generated_sql,
                "error": None,
                "tables_used": list(schema_info.keys())
            }
            
        except Exception as e:
            logger.error(f"Simple SQL generation failed: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e),
                "sql": None,
                "tables_used": []
            }

    def _format_schema_for_prompt(self, schema: dict) -> str:
        """Format schema dict into readable string for LLM"""
        lines = []
        tables = schema["table_names_original"]
        columns = schema["column_names_original"]
        col_types = schema["column_types"]
        
        for idx, table in enumerate(tables):
            table_cols = []
            for col_idx, (tbl_idx, col_name) in enumerate(columns):
                if tbl_idx == idx:
                    col_type = col_types[col_idx] if col_idx < len(col_types) else "unknown"
                    pk_marker = " [PK]" if col_idx in schema.get("primary_keys", []) else ""
                    table_cols.append(f"{col_name} ({col_type}){pk_marker}")
            
            lines.append(f"Table: {table}")
            lines.append(f"  Columns: {', '.join(table_cols)}")
        
        # Add foreign key info
        if schema.get("foreign_keys"):
            lines.append("\nForeign Keys:")
            for src_idx, dst_idx in schema["foreign_keys"]:
                if src_idx < len(columns) and dst_idx < len(columns):
                    src_tbl_idx, src_col = columns[src_idx]
                    dst_tbl_idx, dst_col = columns[dst_idx]
                    if src_tbl_idx < len(tables) and dst_tbl_idx < len(tables):
                        lines.append(f"  {tables[src_tbl_idx]}.{src_col} -> {tables[dst_tbl_idx]}.{dst_col}")
        
        return "\n".join(lines)
