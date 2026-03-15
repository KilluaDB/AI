import os

# Groq
OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
MODEL_NAME = 'llama-3.3-70b-versatile' # Groq

# Gemini
# OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://generativelanguage.googleapis.com/v1beta/openai/")
# OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "AIzaSyAibrGT3yQXBrnaeH2Qg4uLiWuPG1SQyH8")
# MODEL_NAME = 'gemini-2.0-flash' # Gemini


import openai
openai.api_type = "open_ai"
openai.api_base = OPENAI_API_BASE

# set your own api_version
# openai.api_version = "2023-07-01-preview"
# openai.api_version = None
openai.api_key = OPENAI_API_KEY