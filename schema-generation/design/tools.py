"""
Simple Tools for Database Design Agents

Contains:
1. Mermaid generation from conceptual design (parsing-based)
2. Mermaid validation
3. PostgreSQL DDL testing
"""
import os
import re
import json
import subprocess
import tempfile
from typing import Optional, Tuple, Dict, Any
from typing_extensions import Annotated

# Try to import psycopg2
try:
    import psycopg2
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False


# ============== Mermaid Tools ==============

def generate_mermaid_from_conceptual(conceptual_json: dict) -> str:
    """
    Generate Mermaid ER diagram from conceptual design JSON.
    
    Args:
        conceptual_json: Dict with 'Entity Set' and 'Relationship Set'
        
    Returns:
        Mermaid erDiagram code string
    """
    lines = ['erDiagram']
    
    entity_sets = conceptual_json.get('Entity Set', {})
    relationship_sets = conceptual_json.get('Relationship Set', {})
    
    # Cardinality mapping
    card_map = {
        'one-to-one': '||--||',
        'one-to-many': '||--o{',
        'many-to-one': '}o--||',
        'many-to-many': '}o--o{',
    }
    
    # Generate entities
    for entity_name, attributes in entity_sets.items():
        safe_name = entity_name.replace(' ', '_')
        lines.append(f'    {safe_name} {{')
        for i, attr in enumerate(attributes):
            safe_attr = attr.replace(' ', '_')
            attr_type = 'int' if 'id' in attr.lower() else 'string'
            pk = ' PK' if i == 0 or 'id' in attr.lower() else ''
            lines.append(f'        {attr_type} {safe_attr}{pk}')
        lines.append('    }')
    
    # Generate relationships
    for rel_name, rel_def in relationship_sets.items():
        objects = rel_def.get('Object', [])
        cardinality = rel_def.get('Proportional Relationship', 'Many-to-Many').lower().replace(' ', '-')
        
        if len(objects) >= 2:
            e1 = objects[0].replace(' ', '_')
            e2 = objects[1].replace(' ', '_')
            card = card_map.get(cardinality, '}o--o{')
            label = rel_name.replace(' ', '_')
            lines.append(f'    {e1} {card} {e2} : "{label}"')
    
    return '\n'.join(lines)


def extract_conceptual_from_output(output: str) -> Optional[dict]:
    """
    Extract conceptual design JSON from agent output.
    
    Args:
        output: Agent output text
        
    Returns:
        Parsed conceptual design dict or None
    """
    # Try to find JSON with Entity Set
    patterns = [
        r"'output'\s*:\s*(\{[^}]+Entity Set[^}]+\})",
        r'"output"\s*:\s*(\{[^}]+Entity Set[^}]+\})',
        r'(\{[^{}]*"Entity Set"[^{}]*\})',
    ]
    
    # More comprehensive pattern
    try:
        # Find content between 'output': { and the closing }
        match = re.search(r"['\"]output['\"]\s*:\s*(\{.*?\})\s*\}", output, re.DOTALL)
        if match:
            json_str = match.group(1) + '}'
            # Fix quotes
            json_str = json_str.replace("'", '"')
            return json.loads(json_str)
    except:
        pass
    
    # Try simpler extraction
    try:
        start = output.find('"Entity Set"')
        if start == -1:
            start = output.find("'Entity Set'")
        if start != -1:
            # Find the enclosing braces
            brace_start = output.rfind('{', 0, start)
            if brace_start != -1:
                depth = 1
                pos = brace_start + 1
                while pos < len(output) and depth > 0:
                    if output[pos] == '{':
                        depth += 1
                    elif output[pos] == '}':
                        depth -= 1
                    pos += 1
                json_str = output[brace_start:pos].replace("'", '"')
                return json.loads(json_str)
    except:
        pass
    
    return None


async def validate_mermaid(mermaid_code: Annotated[str, "Mermaid diagram code to validate"]) -> Dict[str, Any]:
    """
    Validate Mermaid diagram by running mermaid-cli.
    
    Args:
        mermaid_code: The Mermaid code to validate
        
    Returns:
        Dict with 'valid' boolean and 'message' string
    """
    # Create temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.mmd', delete=False) as f:
        f.write(mermaid_code)
        temp_file = f.name
    
    temp_out = temp_file.replace('.mmd', '.svg')
    
    try:
        # Try mmdc (mermaid-cli)
        result = subprocess.run(
            ['mmdc', '-i', temp_file, '-o', temp_out],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            return {"valid": True, "message": "Mermaid diagram is valid"}
        else:
            return {"valid": False, "message": f"Error: {result.stderr}"}
    except FileNotFoundError:
        # Try docker
        try:
            dir_path = os.path.dirname(temp_file)
            file_name = os.path.basename(temp_file)
            result = subprocess.run(
                ['docker', 'run', '--rm', '-v', f'{dir_path}:/data', 
                 'minlag/mermaid-cli', '-i', f'/data/{file_name}'],
                capture_output=True, text=True, timeout=60
            )
            if result.returncode == 0:
                return {"valid": True, "message": "Mermaid diagram is valid (via Docker)"}
            else:
                return {"valid": False, "message": f"Error: {result.stderr}"}
        except Exception as e:
            # Basic syntax check fallback
            errors = []
            if 'erDiagram' not in mermaid_code and 'erdiagram' not in mermaid_code.lower():
                errors.append("Missing erDiagram declaration")
            if mermaid_code.count('{') != mermaid_code.count('}'):
                errors.append("Unbalanced braces")
            if errors:
                return {"valid": False, "message": f"Syntax errors: {', '.join(errors)}"}
            return {"valid": True, "message": "Basic syntax check passed (mermaid-cli not available)"}
    except subprocess.TimeoutExpired:
        return {"valid": False, "message": "Validation timed out"}
    except Exception as e:
        return {"valid": False, "message": f"Error: {str(e)}"}
    finally:
        try:
            os.unlink(temp_file)
            if os.path.exists(temp_out):
                os.unlink(temp_out)
        except:
            pass


# ============== PostgreSQL Tools ==============

async def test_ddl_on_postgres(
    ddl_statements: Annotated[str, "DDL statements to test (CREATE TABLE, etc.)"],
    database_name: Annotated[str, "Database name"] = "schema_agent"
) -> Dict[str, Any]:
    """
    Test DDL statements on PostgreSQL database.
    
    Args:
        ddl_statements: SQL DDL statements to execute
        database_name: Target database name
        
    Returns:
        Dict with 'success' boolean and 'message' or 'error'
    """
    if not PSYCOPG2_AVAILABLE:
        return {"success": False, "error": "psycopg2 not installed. Run: pip install psycopg2-binary"}
    
    # Get connection params from env
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    user = os.getenv("POSTGRES_USER", "postgres")
    password = os.getenv("POSTGRES_PASSWORD", "postgres")
    
    try:
        conn = psycopg2.connect(
            host=host, port=port, user=user, 
            password=password, database=database_name
        )
        cursor = conn.cursor()
        
        # Split and execute statements
        statements = [s.strip() for s in ddl_statements.split(';') if s.strip() and not s.strip().startswith('--')]
        
        results = []
        for stmt in statements:
            try:
                cursor.execute(stmt)
                conn.commit()
                results.append({"statement": stmt[:50] + "...", "success": True})
            except Exception as e:
                conn.rollback()
                results.append({"statement": stmt[:50] + "...", "success": False, "error": str(e)})
        
        cursor.close()
        conn.close()
        
        all_success = all(r['success'] for r in results)
        return {
            "success": all_success,
            "message": f"Executed {len(results)} statements, {sum(1 for r in results if r['success'])} succeeded",
            "results": results
        }
        
    except Exception as e:
        return {"success": False, "error": f"Connection failed: {str(e)}"}


# ============== Exports ==============

__all__ = [
    'generate_mermaid_from_conceptual',
    'extract_conceptual_from_output',
    'validate_mermaid',
    'test_ddl_on_postgres',
]
