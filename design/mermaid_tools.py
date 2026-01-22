"""
Mermaid Tools for Schema Visualization

This module provides tools for:
- Generating Mermaid ER diagrams from conceptual/logical schema (by parsing, not LLM)
- Extracting JSON conceptual schema from agent output
- Validating Mermaid syntax
- Rendering Mermaid diagrams
"""
import os
import sys
import re
import json
import subprocess
import tempfile
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple


# ============== Mermaid Generation from Schema ==============

# Cardinality mapping to Mermaid notation
CARDINALITY_MAP = {
    'one-to-one': '||--||',
    'one-to-many': '||--o{',
    'many-to-one': '}o--||',
    'many-to-many': '}o--o{',
    '1:1': '||--||',
    '1:n': '||--o{',
    'n:1': '}o--||',
    'n:m': '}o--o{',
    'm:n': '}o--o{',
}

# Data type mapping for Mermaid (simplified types)
MERMAID_TYPE_MAP = {
    'serial': 'int',
    'bigserial': 'bigint',
    'integer': 'int',
    'smallint': 'smallint',
    'bigint': 'bigint',
    'varchar': 'string',
    'text': 'string',
    'char': 'string',
    'boolean': 'bool',
    'date': 'date',
    'time': 'time',
    'timestamp': 'datetime',
    'decimal': 'decimal',
    'numeric': 'decimal',
    'real': 'float',
    'double': 'double',
    'jsonb': 'json',
    'json': 'json',
    'uuid': 'uuid',
    'bytea': 'blob',
}


def infer_mermaid_type(attr_name: str) -> str:
    """
    Infer Mermaid data type from attribute name.
    
    Args:
        attr_name: The attribute name
        
    Returns:
        Mermaid-compatible type string
    """
    attr_lower = attr_name.lower().replace(' ', '_')
    
    # ID fields
    if attr_lower.endswith('_id') or attr_lower == 'id':
        return 'int'
    
    # String fields
    if any(x in attr_lower for x in ['name', 'title', 'description', 'address', 'email', 'text', 'content']):
        return 'string'
    
    # Numeric fields
    if any(x in attr_lower for x in ['count', 'quantity', 'amount', 'number', 'age', 'credits', 'score']):
        return 'int'
    
    if any(x in attr_lower for x in ['price', 'cost', 'salary', 'rate', 'percentage']):
        return 'decimal'
    
    # Date/Time fields
    if any(x in attr_lower for x in ['date', 'birth', 'dob']):
        return 'date'
    
    if any(x in attr_lower for x in ['time', 'hour']):
        return 'time'
    
    if any(x in attr_lower for x in ['timestamp', '_at', 'created', 'updated', 'modified']):
        return 'datetime'
    
    # Boolean fields
    if attr_lower.startswith('is_') or attr_lower.startswith('has_') or attr_lower in ['active', 'enabled', 'deleted']:
        return 'bool'
    
    return 'string'


def sanitize_mermaid_name(name: str) -> str:
    """
    Sanitize a name for use in Mermaid diagrams.
    
    Args:
        name: The name to sanitize
        
    Returns:
        Sanitized name (alphanumeric and underscores only)
    """
    # Replace spaces with underscores
    sanitized = name.replace(' ', '_')
    # Remove any non-alphanumeric characters except underscores
    sanitized = re.sub(r'[^a-zA-Z0-9_]', '', sanitized)
    return sanitized


def generate_mermaid_from_conceptual(conceptual_schema: Dict[str, Any]) -> str:
    """
    Generate Mermaid ER diagram code from conceptual schema.
    
    Args:
        conceptual_schema: Dictionary with 'Entity Set' and 'Relationship Set'
        
    Returns:
        Mermaid ER diagram code string
    """
    lines = ['erDiagram']
    
    entity_sets = conceptual_schema.get('Entity Set', {})
    relationship_sets = conceptual_schema.get('Relationship Set', {})
    
    # Generate entity definitions
    for entity_name, attributes in entity_sets.items():
        safe_name = sanitize_mermaid_name(entity_name)
        lines.append(f'    {safe_name} {{')
        
        for i, attr in enumerate(attributes):
            safe_attr = sanitize_mermaid_name(attr)
            attr_type = infer_mermaid_type(attr)
            
            # Mark first attribute as PK (typically ID)
            if i == 0 or 'id' in attr.lower():
                lines.append(f'        {attr_type} {safe_attr} PK')
            else:
                lines.append(f'        {attr_type} {safe_attr}')
        
        lines.append('    }')
        lines.append('')
    
    # Generate relationship definitions
    for rel_name, rel_def in relationship_sets.items():
        objects = rel_def.get('Object', [])
        cardinality = rel_def.get('Proportional Relationship', 'Many-to-Many').lower().replace(' ', '-')
        rel_attributes = rel_def.get('Relationship Attribute', [])
        
        if len(objects) >= 2:
            entity1 = sanitize_mermaid_name(objects[0])
            entity2 = sanitize_mermaid_name(objects[1])
            
            # Get Mermaid cardinality notation
            mermaid_card = CARDINALITY_MAP.get(cardinality, '}o--o{')
            
            # Create relationship label
            rel_label = sanitize_mermaid_name(rel_name)
            if rel_attributes:
                rel_label += f" ({', '.join(rel_attributes)})"
            
            lines.append(f'    {entity1} {mermaid_card} {entity2} : "{rel_label}"')
    
    return '\n'.join(lines)


def generate_mermaid_from_logical(logical_schema: Dict[str, Any]) -> str:
    """
    Generate Mermaid ER diagram code from logical schema.
    
    Args:
        logical_schema: Dictionary with table definitions including Attribute, Primary key, Foreign key
        
    Returns:
        Mermaid ER diagram code string
    """
    lines = ['erDiagram']
    
    # Track foreign key relationships
    relationships = []
    
    # Generate table definitions
    for table_name, table_def in logical_schema.items():
        safe_name = sanitize_mermaid_name(table_name)
        attributes = table_def.get('Attribute', [])
        primary_keys = table_def.get('Primary key', [])
        foreign_keys = table_def.get('Foreign key', {})
        
        lines.append(f'    {safe_name} {{')
        
        for attr in attributes:
            safe_attr = sanitize_mermaid_name(attr)
            attr_type = infer_mermaid_type(attr)
            
            # Determine key markers
            markers = []
            if attr in primary_keys:
                markers.append('PK')
            if attr in foreign_keys:
                markers.append('FK')
            
            marker_str = ' "' + ','.join(markers) + '"' if markers else ''
            lines.append(f'        {attr_type} {safe_attr}{marker_str}')
        
        lines.append('    }')
        lines.append('')
        
        # Collect relationships from foreign keys
        for fk_attr, ref_info in foreign_keys.items():
            for ref_table, ref_attr in ref_info.items():
                safe_ref_table = sanitize_mermaid_name(ref_table)
                relationships.append((safe_name, safe_ref_table, fk_attr))
    
    # Add relationships
    for from_table, to_table, fk_attr in relationships:
        lines.append(f'    {from_table} }}o--|| {to_table} : "has"')
    
    return '\n'.join(lines)


# ============== JSON Schema Extraction ==============

def extract_conceptual_json(text: str) -> Optional[Dict[str, Any]]:
    """
    Extract conceptual design JSON from agent output text.
    
    Args:
        text: Agent output text containing conceptual design
        
    Returns:
        Parsed conceptual design dictionary or None
    """
    # Try to find JSON in the text
    patterns = [
        # Pattern 1: Look for 'output' section with Entity Set and Relationship Set
        r'\{[^{}]*["\']output["\'][^{}]*\{[^{}]*["\']Entity Set["\'][^{}]*\}[^{}]*\}',
        # Pattern 2: Direct Entity Set and Relationship Set
        r'\{[^{}]*["\']Entity Set["\'][^{}]*["\']Relationship Set["\'][^{}]*\}',
        # Pattern 3: Find any JSON block
        r'```json\s*(.*?)```',
        r'\{[\s\S]*?"Entity Set"[\s\S]*?\}',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text, re.DOTALL)
        for match in matches:
            try:
                # Clean the match
                json_str = match.strip()
                if not json_str.startswith('{'):
                    json_str = '{' + json_str
                if not json_str.endswith('}'):
                    json_str = json_str + '}'
                
                parsed = json.loads(json_str.replace("'", '"'))
                
                # Check if it has the expected structure
                if 'output' in parsed:
                    return parsed['output']
                elif 'Entity Set' in parsed:
                    return parsed
                    
            except json.JSONDecodeError:
                continue
    
    # Try more aggressive extraction
    try:
        # Find Entity Set block
        entity_match = re.search(r'["\']Entity Set["\'][\s:]*\{([^}]+(?:\{[^}]*\}[^}]*)*)\}', text, re.DOTALL)
        rel_match = re.search(r'["\']Relationship Set["\'][\s:]*\{([^}]+(?:\{[^}]*\}[^}]*)*)\}', text, re.DOTALL)
        
        if entity_match:
            # Construct JSON manually
            entity_str = '{' + entity_match.group(1) + '}'
            entity_data = json.loads(entity_str.replace("'", '"'))
            
            result = {'Entity Set': entity_data}
            
            if rel_match:
                rel_str = '{' + rel_match.group(1) + '}'
                rel_data = json.loads(rel_str.replace("'", '"'))
                result['Relationship Set'] = rel_data
            
            return result
    except:
        pass
    
    return None


def extract_logical_json(text: str) -> Optional[Dict[str, Any]]:
    """
    Extract logical design JSON from agent output text.
    
    Args:
        text: Agent output text containing logical design
        
    Returns:
        Parsed logical schema dictionary or None
    """
    # Look for schema with Attribute, Primary key patterns
    patterns = [
        r'```json\s*(.*?)```',
        r'\{[^{}]*["\']Attribute["\'][^{}]*["\']Primary key["\'][^{}]*\}',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text, re.DOTALL)
        for match in matches:
            try:
                json_str = match.strip()
                if not json_str.startswith('{'):
                    continue
                
                parsed = json.loads(json_str.replace("'", '"'))
                
                # Check if any value has 'Attribute' key
                if 'output' in parsed:
                    parsed = parsed['output']
                
                for key, value in parsed.items():
                    if isinstance(value, dict) and 'Attribute' in value:
                        return parsed
                        
            except json.JSONDecodeError:
                continue
    
    return None


# ============== Mermaid Validation ==============

def validate_mermaid_syntax(mermaid_code: str) -> Tuple[bool, List[str]]:
    """
    Validate Mermaid diagram syntax.
    
    Args:
        mermaid_code: Mermaid diagram code to validate
        
    Returns:
        Tuple of (is_valid, list of errors)
    """
    errors = []
    
    lines = mermaid_code.strip().split('\n')
    
    if not lines:
        errors.append("Empty Mermaid code")
        return False, errors
    
    # Check for diagram type declaration
    first_line = lines[0].strip().lower()
    valid_diagram_types = ['erdiagram', 'graph', 'sequencediagram', 'classDiagram', 'flowchart']
    
    if not any(dt in first_line for dt in valid_diagram_types):
        errors.append(f"Missing or invalid diagram type. First line: '{lines[0]}'")
    
    # Check for balanced braces
    open_braces = mermaid_code.count('{')
    close_braces = mermaid_code.count('}')
    if open_braces != close_braces:
        errors.append(f"Unbalanced braces: {open_braces} open, {close_braces} close")
    
    # Check for valid relationship syntax in ER diagrams
    if 'erdiagram' in first_line.lower():
        valid_rel_patterns = ['||--||', '||--o{', '}o--||', '}o--o{', '||--o|', '|o--||', '|o--o|']
        
        for i, line in enumerate(lines[1:], 2):
            line = line.strip()
            
            # Skip empty lines and entity definitions
            if not line or line.startswith('{') or line.startswith('}') or '{' in line:
                continue
            
            # Check if it's a relationship line
            if ':' in line and any(rel in line for rel in ['--', '||', 'o{', '}o']):
                # Validate relationship syntax
                has_valid_rel = any(rel in line for rel in valid_rel_patterns)
                if not has_valid_rel:
                    # Check for simple -- relationship
                    if '--' not in line:
                        errors.append(f"Line {i}: Invalid relationship syntax: '{line}'")
    
    return len(errors) == 0, errors


def validate_mermaid_with_cli(mermaid_code: str) -> Tuple[bool, str]:
    """
    Validate Mermaid diagram using mermaid-cli (mmdc).
    
    Args:
        mermaid_code: Mermaid diagram code to validate
        
    Returns:
        Tuple of (is_valid, error_message or success_message)
    """
    # Create temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.mmd', delete=False) as f:
        f.write(mermaid_code)
        temp_input = f.name
    
    temp_output = temp_input.replace('.mmd', '.svg')
    
    try:
        # Try using mmdc directly
        result = subprocess.run(
            ['mmdc', '-i', temp_input, '-o', temp_output],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            return True, "Mermaid syntax is valid"
        else:
            return False, f"Validation error: {result.stderr}"
            
    except FileNotFoundError:
        # Try using Docker
        try:
            directory = os.path.dirname(temp_input)
            filename = os.path.basename(temp_input)
            
            result = subprocess.run(
                [
                    'docker', 'run', '--rm',
                    '-v', f'{directory}:/data',
                    'minlag/mermaid-cli',
                    '-i', f'/data/{filename}'
                ],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                return True, "Mermaid syntax is valid (validated via Docker)"
            else:
                return False, f"Validation error: {result.stderr}"
                
        except FileNotFoundError:
            return False, "mermaid-cli not found. Install with: npm install -g @mermaid-js/mermaid-cli or use Docker"
        except subprocess.TimeoutExpired:
            return False, "Validation timed out"
            
    except subprocess.TimeoutExpired:
        return False, "Validation timed out"
    except Exception as e:
        return False, f"Validation error: {str(e)}"
    finally:
        # Cleanup
        try:
            os.unlink(temp_input)
            if os.path.exists(temp_output):
                os.unlink(temp_output)
        except:
            pass


def render_mermaid_to_svg(mermaid_code: str, output_path: str = None) -> Tuple[bool, str]:
    """
    Render Mermaid diagram to SVG file.
    
    Args:
        mermaid_code: Mermaid diagram code
        output_path: Output SVG file path (optional)
        
    Returns:
        Tuple of (success, output_path or error_message)
    """
    # Create temporary input file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.mmd', delete=False) as f:
        f.write(mermaid_code)
        temp_input = f.name
    
    if output_path is None:
        output_path = temp_input.replace('.mmd', '.svg')
    
    try:
        # Try using mmdc directly
        result = subprocess.run(
            ['mmdc', '-i', temp_input, '-o', output_path],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0 and os.path.exists(output_path):
            return True, output_path
        else:
            # Try Docker fallback
            directory = os.path.dirname(temp_input)
            filename = os.path.basename(temp_input)
            out_filename = os.path.basename(output_path)
            
            result = subprocess.run(
                [
                    'docker', 'run', '--rm',
                    '-v', f'{directory}:/data',
                    'minlag/mermaid-cli',
                    '-i', f'/data/{filename}',
                    '-o', f'/data/{out_filename}'
                ],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0 and os.path.exists(output_path):
                return True, output_path
            else:
                return False, f"Render error: {result.stderr}"
                
    except FileNotFoundError:
        return False, "mermaid-cli not found. Install with: npm install -g @mermaid-js/mermaid-cli"
    except subprocess.TimeoutExpired:
        return False, "Rendering timed out"
    except Exception as e:
        return False, f"Render error: {str(e)}"
    finally:
        # Cleanup temp input
        try:
            os.unlink(temp_input)
        except:
            pass


# ============== High-Level Functions ==============

def conceptual_to_mermaid(agent_output: str, output_file: str = None) -> Tuple[Optional[str], Optional[str]]:
    """
    Extract conceptual schema from agent output and generate Mermaid diagram.
    
    Args:
        agent_output: Full agent output text
        output_file: Optional file path to save the Mermaid code
        
    Returns:
        Tuple of (mermaid_code, saved_file_path)
    """
    # Extract conceptual schema
    conceptual_schema = extract_conceptual_json(agent_output)
    
    if not conceptual_schema:
        print("Could not extract conceptual schema from output")
        return None, None
    
    # Generate Mermaid code
    mermaid_code = generate_mermaid_from_conceptual(conceptual_schema)
    
    # Validate syntax
    is_valid, errors = validate_mermaid_syntax(mermaid_code)
    if not is_valid:
        print(f"Warning: Mermaid validation errors: {errors}")
    
    # Save to file if requested
    saved_path = None
    if output_file:
        with open(output_file, 'w') as f:
            f.write(mermaid_code)
        saved_path = output_file
    elif output_file is None:
        # Auto-generate file path
        output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'er_data')
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        saved_path = os.path.join(output_dir, f"{timestamp}_conceptual.mmd")
        with open(saved_path, 'w') as f:
            f.write(mermaid_code)
    
    return mermaid_code, saved_path


def logical_to_mermaid(agent_output: str, output_file: str = None) -> Tuple[Optional[str], Optional[str]]:
    """
    Extract logical schema from agent output and generate Mermaid diagram.
    
    Args:
        agent_output: Full agent output text
        output_file: Optional file path to save the Mermaid code
        
    Returns:
        Tuple of (mermaid_code, saved_file_path)
    """
    # Extract logical schema
    logical_schema = extract_logical_json(agent_output)
    
    if not logical_schema:
        print("Could not extract logical schema from output")
        return None, None
    
    # Generate Mermaid code
    mermaid_code = generate_mermaid_from_logical(logical_schema)
    
    # Validate syntax
    is_valid, errors = validate_mermaid_syntax(mermaid_code)
    if not is_valid:
        print(f"Warning: Mermaid validation errors: {errors}")
    
    # Save to file if requested
    saved_path = None
    if output_file:
        with open(output_file, 'w') as f:
            f.write(mermaid_code)
        saved_path = output_file
    elif output_file is None:
        # Auto-generate file path
        output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'er_data')
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        saved_path = os.path.join(output_dir, f"{timestamp}_logical.mmd")
        with open(saved_path, 'w') as f:
            f.write(mermaid_code)
    
    return mermaid_code, saved_path


__all__ = [
    # Generation functions
    'generate_mermaid_from_conceptual',
    'generate_mermaid_from_logical',
    'conceptual_to_mermaid',
    'logical_to_mermaid',
    # Extraction functions
    'extract_conceptual_json',
    'extract_logical_json',
    # Validation functions
    'validate_mermaid_syntax',
    'validate_mermaid_with_cli',
    # Rendering functions
    'render_mermaid_to_svg',
    # Utility functions
    'sanitize_mermaid_name',
    'infer_mermaid_type',
]
