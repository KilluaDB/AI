# -*- coding: utf-8 -*-
"""
PostgreSQL variant of ChatManager.
Uses agents_pg (Selector, Decomposer, Refiner) which read schema directly
from PostgreSQL via information_schema instead of tables.json / SQLite.
"""
from core.agents_pg import Selector, Decomposer, Refiner
from core.const import MAX_ROUND, SYSTEM_NAME, SELECTOR_NAME

INIT_LOG__PATH_FUNC = None
LLM_API_FUC = None
try:
    from core import api
    LLM_API_FUC = api.safe_call_llm
    INIT_LOG__PATH_FUNC = api.init_log_path
    print("Use func from core.api in chat_manager_pg.py")
except Exception:
    from core import llm
    LLM_API_FUC = llm.safe_call_llm
    INIT_LOG__PATH_FUNC = llm.init_log_path
    print("Use func from core.llm in chat_manager_pg.py")

import os
import time
from typing import Dict, Any


class ChatManagerPG:
    """ChatManager that connects to PostgreSQL instead of SQLite."""

    def __init__(self, db_config: Dict[str, Any], log_path: str,
                 model_name: str = "gpt-4", dataset_name: str = "bird",
                 lazy: bool = False, without_selector: bool = False):
        self.db_config = db_config
        self.log_path = log_path
        self.model_name = model_name
        self.dataset_name = dataset_name

        if os.getenv("LLM_PING", "0") == "1":
            self._ping_network()

        self.chat_group = [
            Selector(
                db_config=self.db_config,
                model_name=self.model_name,
                dataset_name=dataset_name,
                lazy=lazy,
                without_selector=without_selector,
            ),
            Decomposer(dataset_name=dataset_name),
            Refiner(db_config=self.db_config, dataset_name=dataset_name),
        ]
        INIT_LOG__PATH_FUNC(log_path)

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

    def start(self, user_message: dict):
        start_time = time.time()
        if user_message['send_to'] == SYSTEM_NAME:
            user_message['send_to'] = SELECTOR_NAME
        for _ in range(MAX_ROUND):
            self._chat_single_round(user_message)
            if user_message['send_to'] == SYSTEM_NAME:
                break
        end_time = time.time()
        exec_time = end_time - start_time
        print(f"\033[0;34mExecute {exec_time} seconds\033[0m", flush=True)
