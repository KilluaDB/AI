"""
PostgreSQL Tools for Physical Design Agent

This module provides PostgreSQL-related tools for:
- Database connection and execution
- DDL statement validation and execution
- Data type inference
- Index recommendation
- Self-refinement with error handling
"""
import os
import sys
import re
import json
import asyncio
import subprocess
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple
from typing_extensions import Annotated

# Try to import psycopg2 for direct database connection
try:
    import psycopg2
    from psycopg2 import sql
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False
    print("Warning: psycopg2 not installed. Install with: pip install psycopg2-binary")


# ============== Data Type Inference ==============

# Mapping of common attribute name patterns to PostgreSQL data types
DATA_TYPE_INFERENCE_RULES = {
    # ID fields
    r'(?i)^(id|.*_id|.*id)$': 'SERIAL PRIMARY KEY',
    r'(?i)^(uuid|guid)$': 'UUID DEFAULT gen_random_uuid()',
    
    # String fields
    r'(?i)^(name|title|label)$': 'VARCHAR(255) NOT NULL',
    r'(?i)^(.*_name|.*name)$': 'VARCHAR(255)',
    r'(?i)^(description|desc|summary|content|text|body|comment)$': 'TEXT',
    r'(?i)^(email|e_mail)$': 'VARCHAR(255) UNIQUE',
    r'(?i)^(phone|telephone|mobile|tel)$': 'VARCHAR(20)',
    r'(?i)^(address|addr|location)$': 'TEXT',
    r'(?i)^(url|link|website|uri)$': 'VARCHAR(2048)',
    r'(?i)^(code|.*_code)$': 'VARCHAR(50)',
    r'(?i)^(status|state)$': 'VARCHAR(50) DEFAULT \'active\'',
    r'(?i)^(type|category|kind)$': 'VARCHAR(100)',
    r'(?i)^(password|passwd|pwd)$': 'VARCHAR(255) NOT NULL',
    r'(?i)^(username|user_name|login)$': 'VARCHAR(100) UNIQUE NOT NULL',
    
    # Numeric fields  
    r'(?i)^(age|count|quantity|qty|amount|number|num)$': 'INTEGER',
    r'(?i)^(price|cost|salary|fee|rate|total)$': 'DECIMAL(10,2)',
    r'(?i)^(credits|score|points|rating)$': 'SMALLINT',
    r'(?i)^(percentage|percent|ratio)$': 'DECIMAL(5,2)',
    r'(?i)^(weight|height|length|width|size)$': 'DECIMAL(10,2)',
    r'(?i)^(latitude|lat)$': 'DECIMAL(10,8)',
    r'(?i)^(longitude|lng|lon)$': 'DECIMAL(11,8)',
    
    # Date/Time fields
    r'(?i)^(date|.*_date)$': 'DATE',
    r'(?i)^(time|.*_time|class_time|start_time|end_time)$': 'TIME',
    r'(?i)^(datetime|timestamp|.*_at)$': 'TIMESTAMP',
    r'(?i)^(created_at|create_time|creation_date)$': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP',
    r'(?i)^(updated_at|update_time|modified_at|modification_date)$': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP',
    r'(?i)^(deleted_at|delete_time)$': 'TIMESTAMP',
    r'(?i)^(birth|birthday|dob|date_of_birth)$': 'DATE',
    r'(?i)^(year|.*_year)$': 'SMALLINT',
    
    # Boolean fields
    r'(?i)^(is_.*|has_.*|can_.*|.*_flag|active|enabled|deleted|visible|published)$': 'BOOLEAN DEFAULT FALSE',
    
    # JSON fields
    r'(?i)^(data|metadata|config|settings|options|preferences|extra|json|attributes)$': 'JSONB',
    
    # Binary fields
    r'(?i)^(image|photo|picture|avatar|file|attachment|blob)$': 'BYTEA',
}

# Default type for unrecognized attributes
DEFAULT_DATA_TYPE = 'VARCHAR(255)'


def infer_data_type(attribute_name: str, is_primary_key: bool = False, 
                    is_foreign_key: bool = False, referenced_type: str = None) -> str:
    """
    Infer PostgreSQL data type from attribute name using pattern matching.
    
    Args:
        attribute_name: The name of the attribute
        is_primary_key: Whether this is a primary key
        is_foreign_key: Whether this is a foreign key
        referenced_type: The type of the referenced column (for FK)
        
    Returns:
        PostgreSQL data type string
    """
    # Clean attribute name
    attr_clean = attribute_name.strip().replace(' ', '_')
    
    # If it's a foreign key, match the referenced type
    if is_foreign_key and referenced_type:
        # Strip constraints from referenced type
        base_type = referenced_type.split()[0]
        if base_type == 'SERIAL':
            return 'INTEGER'
        elif base_type == 'BIGSERIAL':
            return 'BIGINT'
        return base_type
    
    # Check against inference rules
    for pattern, data_type in DATA_TYPE_INFERENCE_RULES.items():
        if re.match(pattern, attr_clean):
            # If it's a primary key and matches ID pattern, use SERIAL
            if is_primary_key and 'id' in attr_clean.lower():
                return 'SERIAL PRIMARY KEY'
            return data_type
    
    # If primary key but no pattern matched
    if is_primary_key:
        return 'SERIAL PRIMARY KEY'
    
    return DEFAULT_DATA_TYPE


def infer_schema_data_types(schema: Dict[str, Any]) -> Dict[str, Dict[str, str]]:
    """
    Infer data types for all attributes in a schema.
    
    Args:
        schema: Dictionary containing table definitions with attributes, primary keys, and foreign keys
        
    Returns:
        Dictionary mapping table names to attribute-type mappings
    """
    type_mappings = {}
    
    # First pass: determine primary key types
    pk_types = {}
    for table_name, table_def in schema.items():
        primary_keys = table_def.get('Primary key', [])
        attributes = table_def.get('Attribute', [])
        
        table_types = {}
        for attr in attributes:
            is_pk = attr in primary_keys
            data_type = infer_data_type(attr, is_primary_key=is_pk)
            table_types[attr] = data_type
            if is_pk:
                pk_types[f"{table_name}.{attr}"] = data_type
        
        type_mappings[table_name] = table_types
    
    # Second pass: update foreign key types to match referenced primary keys
    for table_name, table_def in schema.items():
        foreign_keys = table_def.get('Foreign key', {})
        for fk_attr, ref_info in foreign_keys.items():
            for ref_table, ref_attr in ref_info.items():
                ref_key = f"{ref_table}.{ref_attr}"
                if ref_key in pk_types:
                    ref_type = pk_types[ref_key]
                    type_mappings[table_name][fk_attr] = infer_data_type(
                        fk_attr, is_foreign_key=True, referenced_type=ref_type
                    )
    
    return type_mappings


# ============== Index Recommendation ==============

INDEX_RECOMMENDATION_RULES = {
    # Foreign keys should always have indexes
    'foreign_key': {
        'priority': 'HIGH',
        'reason': 'Foreign key columns benefit from indexes for JOIN operations',
        'type': 'btree'
    },
    # Frequently queried columns
    'query_columns': {
        'patterns': [
            r'(?i)^(name|title|status|type|category|email|username)$',
            r'(?i)^(.*_name|.*_status|.*_type)$',
        ],
        'priority': 'MEDIUM',
        'reason': 'Commonly used in WHERE clauses',
        'type': 'btree'
    },
    # Date columns for range queries
    'date_columns': {
        'patterns': [
            r'(?i)^(date|.*_date|created_at|updated_at|.*_time)$',
        ],
        'priority': 'MEDIUM',
        'reason': 'Date columns often used in range queries',
        'type': 'btree'
    },
    # Text search columns
    'text_search': {
        'patterns': [
            r'(?i)^(description|content|body|text|comment)$',
        ],
        'priority': 'LOW',
        'reason': 'Full-text search capability',
        'type': 'gin'
    },
    # JSON columns
    'json_columns': {
        'patterns': [
            r'(?i)^(data|metadata|config|settings|json)$',
        ],
        'priority': 'LOW',
        'reason': 'JSONB indexing for key lookups',
        'type': 'gin'
    },
}


def recommend_indexes(schema: Dict[str, Any], type_mappings: Dict[str, Dict[str, str]]) -> List[Dict[str, Any]]:
    """
    Recommend indexes based on schema analysis.
    
    Args:
        schema: Dictionary containing table definitions
        type_mappings: Dictionary mapping attributes to data types
        
    Returns:
        List of index recommendations
    """
    recommendations = []
    
    for table_name, table_def in schema.items():
        foreign_keys = table_def.get('Foreign key', {})
        attributes = table_def.get('Attribute', [])
        primary_keys = table_def.get('Primary key', [])
        
        # Recommend indexes for foreign keys
        for fk_attr in foreign_keys.keys():
            recommendations.append({
                'table': table_name,
                'column': fk_attr,
                'index_name': f"idx_{table_name.lower()}_{fk_attr.lower().replace(' ', '_')}",
                'type': 'btree',
                'priority': 'HIGH',
                'reason': 'Foreign key - improves JOIN performance',
                'statement': f"CREATE INDEX idx_{table_name.lower()}_{fk_attr.lower().replace(' ', '_')} ON {table_name} ({fk_attr.replace(' ', '_')});"
            })
        
        # Check other columns against patterns
        for attr in attributes:
            if attr in primary_keys or attr in foreign_keys:
                continue
                
            # Check query columns patterns
            for rule_name, rule_config in INDEX_RECOMMENDATION_RULES.items():
                if 'patterns' not in rule_config:
                    continue
                    
                for pattern in rule_config['patterns']:
                    if re.match(pattern, attr):
                        idx_type = rule_config['type']
                        idx_name = f"idx_{table_name.lower()}_{attr.lower().replace(' ', '_')}"
                        
                        if idx_type == 'gin':
                            # GIN index for text search or JSONB
                            data_type = type_mappings.get(table_name, {}).get(attr, '')
                            if 'TEXT' in data_type:
                                statement = f"CREATE INDEX {idx_name} ON {table_name} USING GIN (to_tsvector('english', {attr.replace(' ', '_')}));"
                            elif 'JSONB' in data_type:
                                statement = f"CREATE INDEX {idx_name} ON {table_name} USING GIN ({attr.replace(' ', '_')});"
                            else:
                                statement = f"CREATE INDEX {idx_name} ON {table_name} ({attr.replace(' ', '_')});"
                        else:
                            statement = f"CREATE INDEX {idx_name} ON {table_name} ({attr.replace(' ', '_')});"
                        
                        recommendations.append({
                            'table': table_name,
                            'column': attr,
                            'index_name': idx_name,
                            'type': idx_type,
                            'priority': rule_config['priority'],
                            'reason': rule_config['reason'],
                            'statement': statement
                        })
                        break
    
    # Sort by priority
    priority_order = {'HIGH': 0, 'MEDIUM': 1, 'LOW': 2}
    recommendations.sort(key=lambda x: priority_order.get(x['priority'], 3))
    
    return recommendations


# ============== DDL Generation ==============

def generate_ddl_from_schema(schema: Dict[str, Any], database_name: str = 'schema_db') -> Tuple[str, str]:
    """
    Generate DDL statements from a logical schema with inferred data types.
    
    Args:
        schema: Dictionary containing table definitions
        database_name: Name of the database
        
    Returns:
        Tuple of (DDL statements, Index statements)
    """
    type_mappings = infer_schema_data_types(schema)
    index_recommendations = recommend_indexes(schema, type_mappings)
    
    ddl_statements = []
    
    # Add database creation comment
    ddl_statements.append(f"-- DDL Statements for {database_name}")
    ddl_statements.append(f"-- Generated at {datetime.now().isoformat()}")
    ddl_statements.append("")
    
    # Track table order for foreign key dependencies
    tables_with_fk = []
    tables_without_fk = []
    
    for table_name, table_def in schema.items():
        if table_def.get('Foreign key'):
            tables_with_fk.append(table_name)
        else:
            tables_without_fk.append(table_name)
    
    # Generate tables without foreign keys first
    ordered_tables = tables_without_fk + tables_with_fk
    
    for table_name in ordered_tables:
        table_def = schema[table_name]
        attributes = table_def.get('Attribute', [])
        primary_keys = table_def.get('Primary key', [])
        foreign_keys = table_def.get('Foreign key', {})
        
        # Sanitize table name
        safe_table_name = table_name.replace(' ', '_')
        
        ddl = [f"CREATE TABLE {safe_table_name} ("]
        column_defs = []
        
        for attr in attributes:
            safe_attr = attr.replace(' ', '_')
            data_type = type_mappings[table_name].get(attr, DEFAULT_DATA_TYPE)
            
            # Remove PRIMARY KEY from type if we'll add composite PK later
            if len(primary_keys) > 1 and 'PRIMARY KEY' in data_type:
                data_type = data_type.replace(' PRIMARY KEY', '')
            
            column_defs.append(f"    {safe_attr} {data_type}")
        
        # Add composite primary key if multiple columns
        if len(primary_keys) > 1:
            pk_cols = ', '.join([pk.replace(' ', '_') for pk in primary_keys])
            column_defs.append(f"    PRIMARY KEY ({pk_cols})")
        
        # Add foreign key constraints
        for fk_attr, ref_info in foreign_keys.items():
            for ref_table, ref_attr in ref_info.items():
                safe_fk = fk_attr.replace(' ', '_')
                safe_ref_table = ref_table.replace(' ', '_')
                safe_ref_attr = ref_attr.replace(' ', '_')
                column_defs.append(
                    f"    FOREIGN KEY ({safe_fk}) REFERENCES {safe_ref_table}({safe_ref_attr}) ON DELETE CASCADE"
                )
        
        ddl.append(',\n'.join(column_defs))
        ddl.append(");")
        ddl_statements.append('\n'.join(ddl))
        ddl_statements.append("")
    
    # Generate index statements
    index_statements = []
    index_statements.append("-- Recommended Indexes")
    index_statements.append("")
    
    for idx in index_recommendations:
        index_statements.append(f"-- {idx['priority']}: {idx['reason']}")
        index_statements.append(idx['statement'])
        index_statements.append("")
    
    return '\n'.join(ddl_statements), '\n'.join(index_statements)


# ============== PostgreSQL Connection ==============

class PostgreSQLConnection:
    """PostgreSQL database connection manager."""
    
    def __init__(self, host: str = None, port: str = None, user: str = None,
                 password: str = None, database: str = None):
        self.host = host or os.getenv("POSTGRES_HOST", "localhost")
        self.port = port or os.getenv("POSTGRES_PORT", "5432")
        self.user = user or os.getenv("POSTGRES_USER", "postgres")
        self.password = password or os.getenv("POSTGRES_PASSWORD", "postgres")
        self.database = database or os.getenv("POSTGRES_DATABASE", "schema_agent")
        self.connection = None
        self.cursor = None
    
    def connect(self) -> bool:
        """Establish database connection."""
        if not PSYCOPG2_AVAILABLE:
            print("psycopg2 not available")
            return False
        
        try:
            self.connection = psycopg2.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database
            )
            self.cursor = self.connection.cursor()
            return True
        except Exception as e:
            print(f"Connection error: {e}")
            return False
    
    def disconnect(self):
        """Close database connection."""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
    
    def execute(self, sql: str, params: tuple = None) -> Tuple[bool, Any]:
        """Execute SQL statement."""
        try:
            self.cursor.execute(sql, params)
            self.connection.commit()
            
            # Try to fetch results if it's a SELECT
            try:
                results = self.cursor.fetchall()
                return True, results
            except:
                return True, None
        except Exception as e:
            self.connection.rollback()
            return False, str(e)
    
    def execute_ddl(self, ddl_statements: str) -> List[Dict[str, Any]]:
        """Execute multiple DDL statements with error tracking."""
        results = []
        
        # Split statements by semicolon
        statements = [s.strip() for s in ddl_statements.split(';') if s.strip() and not s.strip().startswith('--')]
        
        for stmt in statements:
            if not stmt:
                continue
            
            success, result = self.execute(stmt)
            results.append({
                'statement': stmt[:100] + '...' if len(stmt) > 100 else stmt,
                'success': success,
                'error': result if not success else None
            })
        
        return results
    
    def validate_ddl(self, ddl_statements: str) -> List[Dict[str, Any]]:
        """Validate DDL statements without executing (dry run)."""
        results = []
        
        # Parse and check syntax
        statements = [s.strip() for s in ddl_statements.split(';') if s.strip() and not s.strip().startswith('--')]
        
        for stmt in statements:
            if not stmt:
                continue
            
            # Basic syntax validation
            errors = []
            
            # Check for common issues
            if 'CREATE TABLE' in stmt.upper():
                # Check for balanced parentheses
                if stmt.count('(') != stmt.count(')'):
                    errors.append("Unbalanced parentheses")
                
                # Check for valid table name
                match = re.search(r'CREATE TABLE\s+(\w+)', stmt, re.IGNORECASE)
                if not match:
                    errors.append("Invalid table name")
            
            elif 'CREATE INDEX' in stmt.upper():
                # Check for ON clause
                if ' ON ' not in stmt.upper():
                    errors.append("Missing ON clause in CREATE INDEX")
            
            results.append({
                'statement': stmt[:100] + '...' if len(stmt) > 100 else stmt,
                'valid': len(errors) == 0,
                'errors': errors
            })
        
        return results


# ============== Agent Tools ==============

async def execute_sql_on_postgres(
    sql_statement: Annotated[str, "The SQL statement to execute"],
    database_name: Annotated[str, "The database name to connect to"] = "schema_agent"
) -> Dict[str, Any]:
    """
    Execute SQL statement on PostgreSQL database.
    
    Args:
        sql_statement: The SQL to execute
        database_name: Target database name
    
    Returns:
        Dictionary with execution status and results
    """
    conn = PostgreSQLConnection(database=database_name)
    
    if not conn.connect():
        return {
            "success": False,
            "error": "Failed to connect to PostgreSQL",
            "suggestion": "Ensure PostgreSQL is running and credentials are correct"
        }
    
    try:
        success, result = conn.execute(sql_statement)
        return {
            "success": success,
            "result": result if success else None,
            "error": result if not success else None
        }
    finally:
        conn.disconnect()


async def execute_ddl_statements(
    ddl_statements: Annotated[str, "DDL statements to execute (CREATE TABLE, etc.)"],
    database_name: Annotated[str, "The database name"] = "schema_agent"
) -> Dict[str, Any]:
    """
    Execute DDL statements on PostgreSQL with error handling and rollback support.
    
    Args:
        ddl_statements: The DDL statements to execute
        database_name: Target database name
    
    Returns:
        Dictionary with execution results for each statement
    """
    conn = PostgreSQLConnection(database=database_name)
    
    if not conn.connect():
        return {
            "success": False,
            "error": "Failed to connect to PostgreSQL",
            "results": []
        }
    
    try:
        results = conn.execute_ddl(ddl_statements)
        all_success = all(r['success'] for r in results)
        
        return {
            "success": all_success,
            "results": results,
            "summary": f"Executed {len(results)} statements, {sum(1 for r in results if r['success'])} successful"
        }
    finally:
        conn.disconnect()


async def validate_ddl_syntax(
    ddl_statements: Annotated[str, "DDL statements to validate"]
) -> Dict[str, Any]:
    """
    Validate DDL statements syntax without executing.
    
    Args:
        ddl_statements: The DDL statements to validate
    
    Returns:
        Dictionary with validation results
    """
    conn = PostgreSQLConnection()
    results = conn.validate_ddl(ddl_statements)
    
    all_valid = all(r['valid'] for r in results)
    
    return {
        "valid": all_valid,
        "results": results,
        "summary": f"Validated {len(results)} statements, {sum(1 for r in results if r['valid'])} valid"
    }


async def infer_and_generate_ddl(
    schema_json: Annotated[str, "JSON string of the logical schema"],
    database_name: Annotated[str, "Name of the database"] = "schema_db"
) -> Dict[str, Any]:
    """
    Infer data types and generate DDL from a logical schema.
    
    Args:
        schema_json: JSON string containing the logical schema
        database_name: Name of the database
    
    Returns:
        Dictionary with generated DDL and index statements
    """
    try:
        schema = json.loads(schema_json)
    except json.JSONDecodeError as e:
        return {
            "success": False,
            "error": f"Invalid JSON: {e}"
        }
    
    ddl_statements, index_statements = generate_ddl_from_schema(schema, database_name)
    type_mappings = infer_schema_data_types(schema)
    index_recommendations = recommend_indexes(schema, type_mappings)
    
    return {
        "success": True,
        "ddl_statements": ddl_statements,
        "index_statements": index_statements,
        "type_mappings": type_mappings,
        "index_recommendations": [
            {
                'table': idx['table'],
                'column': idx['column'],
                'type': idx['type'],
                'priority': idx['priority'],
                'reason': idx['reason']
            }
            for idx in index_recommendations
        ]
    }


async def test_postgres_connection(
    database_name: Annotated[str, "The database name to test"] = "schema_agent"
) -> Dict[str, Any]:
    """
    Test PostgreSQL connection.
    
    Args:
        database_name: Database name to connect to
    
    Returns:
        Dictionary with connection status
    """
    conn = PostgreSQLConnection(database=database_name)
    
    if conn.connect():
        try:
            success, result = conn.execute("SELECT version();")
            if success and result:
                return {
                    "connected": True,
                    "version": result[0][0] if result else "Unknown",
                    "database": database_name
                }
        finally:
            conn.disconnect()
    
    return {
        "connected": False,
        "error": "Failed to connect to PostgreSQL",
        "suggestion": "Check POSTGRES_HOST, POSTGRES_PORT, POSTGRES_USER, POSTGRES_PASSWORD environment variables"
    }


# Export tools for use in agents
POSTGRES_TOOLS = [
    execute_sql_on_postgres,
    execute_ddl_statements,
    validate_ddl_syntax,
    infer_and_generate_ddl,
    test_postgres_connection,
]

__all__ = [
    'infer_data_type',
    'infer_schema_data_types',
    'recommend_indexes',
    'generate_ddl_from_schema',
    'PostgreSQLConnection',
    'execute_sql_on_postgres',
    'execute_ddl_statements',
    'validate_ddl_syntax',
    'infer_and_generate_ddl',
    'test_postgres_connection',
    'POSTGRES_TOOLS',
    'DATA_TYPE_INFERENCE_RULES',
]
