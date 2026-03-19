import os



# Groq
# OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "")
# OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
# MODEL_NAME = 'llama-3.3-70b-versatile' # Groq

# Gemini
# OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "")
# OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
# MODEL_NAME = 'gemini-2.0-flash' # Gemini

# Ollama (OpenAI-compatible local endpoint)

# OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "")
# OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
# MODEL_NAME = os.getenv("LLM_MODEL", "qwen2.5-coder:7b")

# OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "")
# OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
# Default to SQL-specialized model; override via LLM_MODEL if needed
# MODEL_NAME = os.getenv("LLM_MODEL", "mannix/defog-llama3-sqlcoder-8b")

# GitHub Models (OpenAI-compatible) endpoint.
# Set OPENAI_API_BASE in your environment to the GitHub Models base URL.
# Example (you must use your own actual endpoint): https://<your-endpoint>/v1
OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://models.github.ai/inference")

# Prefer GitHub PAT for authentication (falls back to OPENAI_API_KEY if set).
# NOTE: Hard-coding tokens is unsafe; rotate/revoke any exposed PATs.
GH_API_KEY = os.getenv("GITHUB_PAT", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", GH_API_KEY)

# Default model for GitHub Models; override via LLM_MODEL if needed
MODEL_NAME = os.getenv("LLM_MODEL", "gpt-4o")





import openai
openai.api_type = "open_ai"
openai.api_base = OPENAI_API_BASE

# set your own api_version
# openai.api_version = "2023-07-01-preview"
# openai.api_version = None
openai.api_key = OPENAI_API_KEY