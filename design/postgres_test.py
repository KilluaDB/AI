# PostgreSQL Database Test Script
# This script tests the connection to a PostgreSQL database using MCP tools
# 
# Prerequisites:
# 1. PostgreSQL server running
# 2. Install the PostgreSQL MCP server: npm install -g @anthropic-ai/mcp-server-postgres
# 
# To run PostgreSQL MCP server manually:
# POSTGRES_HOST=localhost POSTGRES_PORT=5432 POSTGRES_USER=postgres POSTGRES_PASSWORD=your_password POSTGRES_DATABASE=your_db npx @anthropic-ai/mcp-server-postgres

import asyncio
import os
import sys
from pathlib import Path
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_ext.tools.mcp import StdioServerParams, mcp_server_tools
from autogen_agentchat.agents import AssistantAgent
from autogen_core import CancellationToken
from autogen_agentchat.ui import Console

# Import centralized LLM configuration
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from llm_config import create_model_client, get_api_key, get_model_config


async def main(model_name: str = 'gpt4') -> None:
    """
    Main function to test PostgreSQL connection and execute SQL operations.
    
    Args:
        model_name: The name of the LLM model to use (default: 'gpt4')
    """
    # Create model client using centralized configuration
    model_client = create_model_client(model_name)
    print(f'Finished loading model: {model_name}')

    # PostgreSQL connection parameters
    postgres_params = {
        "host": os.getenv("POSTGRES_HOST", "localhost"),
        "port": os.getenv("POSTGRES_PORT", "5432"),
        "user": os.getenv("POSTGRES_USER", "postgres"),
        "password": os.getenv("POSTGRES_PASSWORD", "postgres"),
        "database": os.getenv("POSTGRES_DATABASE", "schema_agent"),
    }

    print(f"Connecting to PostgreSQL: {postgres_params['host']}:{postgres_params['port']}/{postgres_params['database']}")

    # Create PostgreSQL MCP server parameters
    # Using the official Anthropic PostgreSQL MCP server
    server_params = StdioServerParams(
        command="npx",
        args=[
            "-y",
            "@anthropic-ai/mcp-server-postgres",
        ],
        env={
            "POSTGRES_HOST": postgres_params["host"],
            "POSTGRES_PORT": postgres_params["port"],
            "POSTGRES_USER": postgres_params["user"],
            "POSTGRES_PASSWORD": postgres_params["password"],
            "POSTGRES_DATABASE": postgres_params["database"],
        },
    )

    # Get all available PostgreSQL tools
    tools = await mcp_server_tools(server_params)
    for tool in tools:
        print("Available PostgreSQL tools:", tool._tool)

    # Create an agent that can use the PostgreSQL tools
    agent = AssistantAgent(
        name="postgres_manager",
        model_client=model_client,
        tools=tools,  # type: ignore
        system_message="""You are a PostgreSQL database expert. You can execute SQL queries and help manage PostgreSQL databases.
        
When creating tables, use PostgreSQL-compatible data types:
- Use SERIAL or BIGSERIAL for auto-incrementing primary keys
- Use VARCHAR(n) for variable-length strings
- Use TEXT for long text
- Use INTEGER, BIGINT, SMALLINT for integers
- Use NUMERIC(p,s) or DECIMAL(p,s) for exact decimal numbers
- Use REAL or DOUBLE PRECISION for floating-point numbers
- Use BOOLEAN for true/false values
- Use DATE, TIME, TIMESTAMP for date/time values
- Use JSONB for JSON data

Always use proper PostgreSQL syntax for:
- Table creation with constraints
- Index creation
- Foreign key references
"""
    )

    # Example task: Create a course table
    task = """
    Help me create a new course table with the following schema:
    Course(course_id, course_name, instructor_id, credits)
    
    Where:
    - course_id is the primary key (auto-incrementing)
    - course_name is a string (max 200 characters)
    - instructor_id is a foreign key reference
    - credits is an integer
    
    Please define appropriate PostgreSQL data types and constraints.
    """

    await Console(
        agent.run_stream(task=task, cancellation_token=CancellationToken())
    )

    print('Finished PostgreSQL test')


async def test_connection() -> bool:
    """
    Test if PostgreSQL connection is working.
    
    Returns:
        True if connection is successful, False otherwise
    """
    import subprocess
    
    postgres_params = {
        "host": os.getenv("POSTGRES_HOST", "localhost"),
        "port": os.getenv("POSTGRES_PORT", "5432"),
        "user": os.getenv("POSTGRES_USER", "postgres"),
        "password": os.getenv("POSTGRES_PASSWORD", "postgres"),
        "database": os.getenv("POSTGRES_DATABASE", "schema_agent"),
    }
    
    try:
        # Try to connect using psql
        env = os.environ.copy()
        env["PGPASSWORD"] = postgres_params["password"]
        
        result = subprocess.run(
            [
                "psql",
                "-h", postgres_params["host"],
                "-p", postgres_params["port"],
                "-U", postgres_params["user"],
                "-d", postgres_params["database"],
                "-c", "SELECT 1;"
            ],
            env=env,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            print("✓ PostgreSQL connection successful")
            return True
        else:
            print(f"✗ PostgreSQL connection failed: {result.stderr}")
            return False
            
    except FileNotFoundError:
        print("✗ psql command not found. Please install PostgreSQL client.")
        return False
    except subprocess.TimeoutExpired:
        print("✗ PostgreSQL connection timed out")
        return False
    except Exception as e:
        print(f"✗ PostgreSQL connection error: {e}")
        return False


if __name__ == "__main__":
    # First test the connection
    import asyncio
    
    print("Testing PostgreSQL connection...")
    if asyncio.run(test_connection()):
        print("\nRunning main agent task...")
        asyncio.run(main())
    else:
        print("\nPlease ensure PostgreSQL is running and credentials are correct.")
        print("You can set connection parameters via environment variables:")
        print("  POSTGRES_HOST, POSTGRES_PORT, POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DATABASE")
