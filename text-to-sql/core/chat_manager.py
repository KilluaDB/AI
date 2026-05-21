# -*- coding: utf-8 -*-
"""
PostgreSQL variant of ChatManager.
Uses agents_pg (Selector, Decomposer, Refiner) which read schema directly
from PostgreSQL via information_schema instead of tables.json / SQLite.
"""
from core.agents import Selector, Decomposer, Refiner
from core.const import MAX_ROUND, SYSTEM_NAME, SELECTOR_NAME

INIT_LOG_PATH_FUNC = None
LLM_API_FUC = None
try:
    from core import api
    LLM_API_FUC = api.safe_call_llm
    INIT_LOG_PATH_FUNC = api.init_log_path
    print("Use func from core.api in chat_manager_pg.py")
except Exception:
    from core import llm
    LLM_API_FUC = llm.safe_call_llm
    INIT_LOG_PATH_FUNC = llm.init_log_path
    print("Use func from core.llm in chat_manager_pg.py")

import os
import tempfile
import time
from typing import Any, Dict, Optional
import logging
logger = logging.getLogger(__name__)


class ChatManager(object):
    def __init__(self, data_path: str, tables_json_path: str, log_path: str, model_name: str, dataset_name:str, lazy: bool=False, without_selector: bool=False):
        self.data_path = data_path  # root path to database dir, including all databases
        self.tables_json_path = tables_json_path # path to table description json file
        self.log_path = log_path  # path to record important printed content during running
        self.model_name = model_name  # name of base LLM called by agent
        self.dataset_name = dataset_name

        # Optionally ping the LLM backend when explicitly enabled.
        # By default, this is disabled to avoid unnecessary or hanging "Hello world" calls.
        if os.getenv("LLM_PING", "0") == "1":
            self.ping_network()
        self.chat_group = [
            Selector(data_path=self.data_path, tables_json_path=self.tables_json_path, model_name=self.model_name, dataset_name=dataset_name, lazy=lazy, without_selector=without_selector),
            Decomposer(dataset_name=dataset_name),
            Refiner(data_path=self.data_path, dataset_name=dataset_name)
        ]
        INIT_LOG_PATH_FUNC(log_path)

    def ping_network(self):
        # check network status
        print("Checking network status...", flush=True)
        try:
            _ = LLM_API_FUC("Hello world!")
            print("Network is available", flush=True)
        except Exception as e:
            raise Exception(f"Network is not available: {e}")

    def _chat_single_round(self, message: dict):
        # we use `dict` type so value can be changed in the function
        for agent in self.chat_group:  # check each agent in the group
            if message['send_to'] == agent.name:
                agent.talk(message)

    def start(self, user_message: dict):
        # we use `dict` type so value can be changed in the function
        start_time = time.time()
        if user_message['send_to'] == SYSTEM_NAME:  # in the first round, pass message to prune
            user_message['send_to'] = SELECTOR_NAME
        for _ in range(MAX_ROUND):  # start chat in group
            self._chat_single_round(user_message)
            if user_message['send_to'] == SYSTEM_NAME:  # should terminate chat
                break
        end_time = time.time()
        exec_time = end_time - start_time
        print(f"\033[0;34mExecute {exec_time} seconds\033[0m", flush=True)

class ChatManagerPG:
    """ChatManager that connects to PostgreSQL instead of SQLite."""

    def __init__(
        self, 
        db_config: Dict[str, Any], 
        schema_info: Dict[str, Any] = None,
        log_path: str = "",
        model_name: str = "gpt-4", 
        dataset_name: str = "bird",
        lazy: bool = False, 
        without_selector: bool = False
    ):
        self.db_config = db_config
        self.log_path = log_path
        self.model_name = model_name
        self.dataset_name = dataset_name
        self.schema_info = schema_info

        if os.getenv("LLM_PING", "0") == "1":
            self._ping_network()

        self.chat_group = [
            Selector(
                db_config=self.db_config,
                schema_info=self.schema_info,
                model_name=self.model_name,
                dataset_name=dataset_name,
                lazy=lazy,
                without_selector=without_selector,
            ),
            Decomposer(dataset_name=dataset_name),
            Refiner(db_config=self.db_config, dataset_name=dataset_name),
        ]

        if INIT_LOG_PATH_FUNC and log_path:
            INIT_LOG_PATH_FUNC(log_path)

    def _ping_network(self):
        print("Checking network status...", flush=True)
        try:
            _ = LLM_API_FUC("Hello world!")
            print("Network is available", flush=True)
        except Exception as e:
            raise Exception(f"Network is not available: {e}")

    def _chat_single_round(self, message: dict):
        for agent in self.chat_group:
            if message['send_to'] == agent.name:
                agent.talk(message)
                break

    def start(self, user_message: dict):
        """
        Start multi-agent SQL generation.
        
        Args:
            user_message: {
                'query': natural language question,
                'evidence': additional context (optional),
                'extracted_schema': pre-extracted schema (optional),
                'send_to': initial agent (default: SYSTEM_NAME)
            }
        
        Returns:
            Updated message dict with 'pred' containing generated SQL
        """
        logger.info("\n" + "#"*70)
        logger.info(f"\033[1;36m### MULTI-AGENT SQL GENERATION STARTED ###\033[0m")
        logger.info(f"Query: {user_message.get('query', '')}")
        logger.info(f"Evidence: {user_message.get('evidence', 'None')}")
        logger.info("#"*70 + "\n")
        
        # Route to Selector first
        if user_message.get('send_to') == SYSTEM_NAME or not user_message.get('send_to'):
            user_message['send_to'] = SELECTOR_NAME
        
        # Multi-round chat
        for round_num in range(MAX_ROUND):
            logger.info(f"\n>>> Round {round_num + 1}/{MAX_ROUND} - Current agent: {user_message['send_to']}")
            self._chat_single_round(user_message)
            if user_message['send_to'] == SYSTEM_NAME:
                logger.info(f"\n>>> Pipeline complete after {round_num + 1} rounds")
                break
        
        logger.info("\n" + "#"*70)
        logger.info(f"\033[1;36m### MULTI-AGENT SQL GENERATION COMPLETE ###\033[0m")
        logger.info(f"Final SQL: {user_message.get('pred', user_message.get('final_sql', 'None'))}")
        logger.info(f"Pruned: {user_message.get('pruned', False)}")
        logger.info(f"Fixed: {user_message.get('fixed', False)}")
        logger.info(f"Try times: {user_message.get('try_times', 0)}")
        logger.info("#"*70 + "\n")
        
        return user_message

# It's outside the class
def generate_sql_with_agents(
    query: str,
    db_config: Dict[str, Any],
    schema_info: Dict[str, Any] = None,
    evidence: str = "",
    model_name: str = "gpt-4",
    dataset_name: str = "custom",
    without_selector: bool = False
) -> Dict[str, Any]:
    """
    Convenience function to generate SQL using multi-agent system.
    
    Args:
        query: Natural language question
        db_config: PostgreSQL connection config
        schema_info: Pre-extracted schema (optional)
        evidence: Additional context
        model_name: LLM model name
        dataset_name: Dataset name for templates
        without_selector: Skip schema pruning
    
    Returns:
        Dict with 'sql', 'success', 'error'
    """
    logger.info(f"\n{'*'*70}")
    logger.info(f"\\033[1;34m[generate_sql_with_agents] Starting\\033[0m")
    logger.info(f"Query: {query}")
    logger.info(f"DB: {db_config.get('dbname', 'unknown')}")
    logger.info(f"Model: {model_name}")
    logger.info(f"Schema tables: {list(schema_info.keys()) if schema_info else 'Not provided'}")
    logger.info(f"{'*'*70}\\n")
    
    try:
        manager = ChatManagerPG(
            db_config=db_config,
            schema_info=schema_info,
            model_name=model_name,
            dataset_name=dataset_name,
            lazy=False,
            without_selector=without_selector
        )
        
        message = {
            'db_id': db_config.get('dbname', 'database'),
            'query': query,
            'evidence': evidence,
            'extracted_schema': {},
            'send_to': SYSTEM_NAME
        }
        
        result = manager.start(message)
        
        sql = result.get('pred', result.get('final_sql', ''))
        
        output = {
            'sql': sql,
            'success': 'error' not in sql.lower() if sql else False,
            'error': None,
            'pruned': result.get('pruned', False),
            'fixed': result.get('fixed', False),
            'try_times': result.get('try_times', 0)
        }
        
        logger.info(f"\n{'*'*70}")
        logger.info(f"\033[1;34m[generate_sql_with_agents] Complete\033[0m")
        logger.info(f"Success: {output['success']}")
        logger.info(f"SQL: {output['sql']}")
        logger.info(f"{'*'*70}\n")
        
        return output
        
    except Exception as e:
        logger.error(f"\\n{'*'*70}")
        logger.error(f"\\033[1;31m[generate_sql_with_agents] FAILED\\033[0m")
        logger.error(f"Error: {str(e)}")
        import traceback
        logger.error(f"Traceback:\\n{traceback.format_exc()}")
        logger.error(f"{'*'*70}\\n")
        
        return {
            'sql': None,
            'success': False,
            'error': str(e)
        }