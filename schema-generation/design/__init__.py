"""
Physical Design Module

This module contains the physical database design components:
- Agent chat for physical design
- LLM tools for Mermaid ER diagram and JSON schema generation
- PostgreSQL testing utilities
"""

from .agent_chat_physical import main as run_physical_design
from .llm_tools import (
    # Extraction functions
    extract_conceptual_design,
    extract_code_block,
    extract_mermaid_from_output,
    extract_ddl_from_output,
    extract_json_from_output,
    # Generation functions
    generate_mermaid_er,
    generate_json_schema,
    generate_er,
)

__all__ = [
    'run_physical_design',
    # Extraction functions
    'extract_conceptual_design',
    'extract_code_block',
    'extract_mermaid_from_output',
    'extract_ddl_from_output',
    'extract_json_from_output',
    # Generation functions
    'generate_mermaid_er',
    'generate_json_schema',
    'generate_er',
]
