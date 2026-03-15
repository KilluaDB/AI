import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.llm import safe_call_llm, init_log_path
from core.utils import parse_sql_from_string

class TextToSQLService:
    def __init__(self, api_key: str = "ollama", model_name: str = "qwen2.5-coder:7b", api_base: str = "http://localhost:11434/v1"):
        """Initialize the Text-to-SQL service"""
        from core import api_config
        api_config.MODEL_NAME = model_name
        api_config.openai.api_key = api_key
        api_config.openai.api_base = api_base
        api_config.openai.api_type = "open_ai"
        
    def get_schema_from_db(self, db_config: dict) -> dict:
        """
        Extract schema from user's PostgreSQL database in Docker container
        
        db_config = {
            "host": "localhost",
            "port": 5432,
            "database": "user_db",
            "user": "postgres",
            "password": "secret"
        }
        """
        import psycopg2 # type: ignore
        
        schema = {
            "db_id": db_config.get("database", "user_db"),
            "table_names_original": [],
            "column_names_original": [[-1, "*"]],
            "column_types": ["text"],
            "foreign_keys": [],
            "primary_keys": []
        }
        
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
        return schema
    
    def generate_sql(self, question: str, schema: dict, hint: str = "") -> str:
        """
        Convert natural language question to SQL query using LLM
        """
        schema_str = self._format_schema_for_prompt(schema)
        
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

### SQL Query:
"""
        
        response = safe_call_llm(prompt)
        sql = parse_sql_from_string(response)
        return sql if sql else response.strip()
    
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
                    pk_marker = " [PK]" if col_idx in schema["primary_keys"] else ""
                    table_cols.append(f"{col_name} ({col_type}){pk_marker}")
            
            lines.append(f"Table: {table}")
            lines.append(f"  Columns: {', '.join(table_cols)}")
        
        # Add foreign key info
        if schema["foreign_keys"]:
            lines.append("\nForeign Keys:")
            for src_idx, dst_idx in schema["foreign_keys"]:
                src_tbl_idx, src_col = columns[src_idx]
                dst_tbl_idx, dst_col = columns[dst_idx]
                lines.append(f"  {tables[src_tbl_idx]}.{src_col} -> {tables[dst_tbl_idx]}.{dst_col}")
        
        return "\n".join(lines)