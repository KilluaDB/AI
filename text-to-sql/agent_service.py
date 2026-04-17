"""
Agent Service - Integrates the existing multi-agent system (Decomposer, Selector, Refiner)
with FastAPI for text-to-SQL generation.
"""

import sys
import os
import openai
import json
import tempfile
import logging

# Add project root to path to import core modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import psycopg2  # pyright: ignore[reportMissingModuleSource]

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
        
        # Use provided values or fall back to api_config defaults
        self.api_key = api_key or os.getenv("LLM_API_KEY")
        self.model_name = model_name or os.getenv("LLM_MODEL", "gpt-4o")
        self.api_base = api_base or os.getenv("LLM_API_BASE", "https://models.github.ai/inference")
        
        if not self.api_key:
            logger.error("No LLM_API_KEY found in arguments or environment variables!")
            # it's better to raise an error early than crash later
            raise ValueError("LLM_API_KEY is required to start the Agent Service.")

        self._configure_llm()
        
    def _configure_llm(self):
        """Configure the LLM API settings"""
        openai.api_key = self.api_key
        openai.api_base = self.api_base
        openai.api_type = "open_ai"
        logger.info(f"LLM configured: model={self.model_name}, api_base={self.api_base}")

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
        from core.chat_manager import generate_sql_with_agents as pg_generate_sql
        from core.utils import get_schema_info
        
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