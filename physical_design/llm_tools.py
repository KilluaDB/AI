"""
LLM Tools for Schema Generation

This module provides LLM-powered tools for:
- Mermaid ER diagram generation
- JSON schema generation
- Text extraction utilities
"""
import os
import sys
import re
import json
from datetime import datetime
from typing import Optional, Dict, Any, Tuple

from openai import OpenAI

# Import centralized LLM configuration
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from llm_config import get_model_config, get_api_key


# ============== Extraction Functions ==============

def extract_conceptual_design(text: str) -> Optional[str]:
    """Extract conceptual design section from the agent output.
    
    Args:
        text: Full agent output text
        
    Returns:
        Extracted conceptual design section or None
    """
    pattern = r"## 2\. Conceptual Design(.*?)## 3\. Logical Design"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return None


def extract_code_block(text: str) -> Optional[str]:
    """Extract code block from text.
    
    Args:
        text: Text containing a code block
        
    Returns:
        Content of the code block or None
    """
    pattern = r"```(?:\w*)\n(.*?)```"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return None


def extract_mermaid_from_output(output_string: str) -> Optional[str]:
    """Extract mermaid diagram code from the agent output.
    
    Args:
        output_string: Agent output containing mermaid code
        
    Returns:
        Mermaid code or None
    """
    mermaid_match = re.search(r'```mermaid\s*(.*?)```', output_string, re.DOTALL)
    if mermaid_match:
        return mermaid_match.group(1).strip()
    return None


def extract_ddl_from_output(output_string: str) -> Optional[str]:
    """Extract DDL statements from the agent output.
    
    Args:
        output_string: Agent output containing SQL DDL statements
        
    Returns:
        Combined DDL statements or None
    """
    ddl_matches = re.findall(r"```sql\s*(.*?)```", output_string, re.DOTALL | re.IGNORECASE)
    if ddl_matches:
        ddl_statements = '\n\n'.join([m.strip() for m in ddl_matches if 'CREATE' in m.upper()])
        return ddl_statements if ddl_statements else None
    return None


def extract_json_from_output(output_string: str) -> Optional[str]:
    """Extract JSON code block from the agent output.
    
    Args:
        output_string: Agent output containing JSON
        
    Returns:
        JSON string or None
    """
    json_match = re.search(r'```json\s*(.*?)```', output_string, re.DOTALL)
    if json_match:
        return json_match.group(1).strip()
    return None


# ============== LLM Generation Functions ==============

def generate_mermaid_er(conceptual_design: str, model_name: str = 'deepseek', 
                        output_dir: Optional[str] = None) -> Tuple[Optional[str], Optional[str]]:
    """Generate ER diagram using the specified LLM model.
    
    Args:
        conceptual_design: The conceptual design text to convert to ER diagram
        model_name: LLM model to use (default: 'deepseek')
        output_dir: Directory to save the mermaid file (default: physical_design/er_data)
        
    Returns:
        Tuple of (mermaid_code, saved_file_path)
    """
    if not conceptual_design:
        return None, None
    
    # Get model configuration from centralized config
    config = get_model_config(model_name)
    api_key = get_api_key(model_name)
    
    client = OpenAI(
        api_key=api_key,
        base_url=config.get('base_url', 'https://api.openai.com/v1/')
    )
    
    prompt = """You are a professional database designer.

Given the following Entity Sets and Relationship Sets, please generate a complete and accurate Mermaid ER diagram code using `erDiagram` syntax. Follow these strict rules:

1. Use `PK` and `FK` to mark primary and foreign keys in the entity or relationship tables.
2. Use `||--o{`, `||--||`, `o{--o{` etc. to represent correct cardinality:
   - `||--o{` means one-to-many
   - `||--||` means one-to-one
   - `o{--o{` means many-to-many
3. For relationship sets, if needed, create a separate entity-like table to store relationship attributes and foreign keys.
4. Do not include any extra explanation or markdown syntax like ```mermaid. Just return the raw ER diagram code.
5. Use appropriate attribute types like `int`, `string`, `date`, `float`, etc., based on the names.
"""
    
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt + conceptual_design,
                }
            ],
            model=config['model_name'],
        )
        
        mermaid_code = extract_code_block(chat_completion.choices[0].message.content)
        if mermaid_code is None:
            mermaid_code = chat_completion.choices[0].message.content
        
        # Determine output directory
        if output_dir is None:
            output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'er_data')
        
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = f"{timestamp}.mmd"
        save_file_path = os.path.join(output_dir, file_name)
        
        with open(save_file_path, "w", encoding="utf-8") as f:
            f.write(mermaid_code)
        
        print(f"Mermaid code saved to {save_file_path}")
        
        return mermaid_code, save_file_path
        
    except Exception as e:
        print(f"Error generating mermaid: {e}")
        return None, None


def generate_json_schema(conceptual_design: str, ddl_statements: Optional[str] = None, 
                         model_name: str = 'deepseek') -> Optional[Dict[str, Any]]:
    """Generate JSON schema representation using LLM.
    
    Args:
        conceptual_design: The conceptual design text
        ddl_statements: Optional DDL statements for additional context
        model_name: LLM model to use (default: 'deepseek')
        
    Returns:
        JSON schema dictionary or None
    """
    if not conceptual_design:
        return None
    
    # Get model configuration from centralized config
    config = get_model_config(model_name)
    api_key = get_api_key(model_name)
    
    client = OpenAI(
        api_key=api_key,
        base_url=config.get('base_url', 'https://api.openai.com/v1/')
    )
    
    prompt = """You are a professional database designer.

Given the following Entity Sets, Relationship Sets, and DDL statements, please generate a complete JSON schema representation. Follow these strict rules:

1. Return ONLY valid JSON, no markdown or explanation.
2. The JSON structure should be:
{
  "entities": [
    {
      "name": "EntityName",
      "attributes": ["attr1", "attr2"],
      "primary_key": ["pk_attr"],
      "description": "Brief description"
    }
  ],
  "relationships": [
    {
      "name": "RelationshipName",
      "from_entity": "Entity1",
      "to_entity": "Entity2",
      "cardinality": "one-to-many|many-to-many|one-to-one",
      "attributes": ["attr1"]
    }
  ],
  "tables": [
    {
      "name": "TableName",
      "columns": [
        {"name": "col1", "type": "INT", "constraints": ["PRIMARY KEY", "NOT NULL"]}
      ],
      "primary_key": ["col1"],
      "foreign_keys": [
        {"column": "fk_col", "references_table": "OtherTable", "references_column": "id"}
      ],
      "indexes": ["idx_name"]
    }
  ],
  "ddl_statements": "CREATE TABLE ...",
  "index_statements": "CREATE INDEX ..."
}
3. Extract all entity information from the conceptual design.
4. Extract table structure from DDL statements if provided.
5. Be accurate and complete.

Conceptual Design:
"""
    
    ddl_section = f"\n\nDDL Statements:\n{ddl_statements}" if ddl_statements else ""
    
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt + conceptual_design + ddl_section,
                }
            ],
            model=config['model_name'],
        )
        
        response_content = chat_completion.choices[0].message.content
        
        # Try to extract JSON from code block first
        json_str = extract_json_from_output(f"```json\n{response_content}\n```")
        if not json_str:
            json_str = extract_code_block(response_content)
        if not json_str:
            json_str = response_content
        
        # Clean up the JSON string
        json_str = json_str.strip()
        
        # Parse JSON
        schema_json = json.loads(json_str)
        return schema_json
        
    except json.JSONDecodeError as e:
        print(f"JSON parsing error: {e}")
        return None
    except Exception as e:
        print(f"Error generating JSON schema: {e}")
        return None


# Keep backward compatibility with test_mermaid.py's generate_er function
def generate_er(requirement_text: str, model_name: str = 'deepseek') -> Optional[str]:
    """Generate ER diagram (backward compatible with test_mermaid.py).
    
    Args:
        requirement_text: The conceptual design text to convert to ER diagram
        model_name: Model to use (default: 'deepseek')
        
    Returns:
        Path to the generated SVG file or mmd file
    """
    mermaid_code, save_file_path = generate_mermaid_er(requirement_text, model_name)
    
    if not save_file_path:
        return None
    
    # Try to generate SVG using mermaid-cli docker
    try:
        import subprocess
        directory = os.path.dirname(save_file_path)
        file_name = os.path.basename(save_file_path)
        
        cmd = [
            "sudo", "docker", "run",
            "--user", f"{os.getuid()}:{os.getgid()}",
            "-v", f"{directory}:/data",
            "minlag/mermaid-cli",
            "-i", f"/data/{file_name}"
        ]
        
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(result.stdout)
        return save_file_path + '.svg'
    except subprocess.CalledProcessError as e:
        print(f"Docker mermaid-cli error: {e.stderr}")
        return save_file_path
    except Exception as e:
        print(f"Error running mermaid-cli: {e}")
        return save_file_path


__all__ = [
    # Extraction functions
    'extract_conceptual_design',
    'extract_code_block',
    'extract_mermaid_from_output',
    'extract_ddl_from_output',
    'extract_json_from_output',
    # Generation functions
    'generate_mermaid_er',
    'generate_json_schema',
    'generate_er',  # Backward compatibility
]
