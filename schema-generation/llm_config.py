import os
from typing import Dict, Any, Optional

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    # Load .env from project root
    load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env'))
except ImportError:
    print("Warning: python-dotenv not installed. Please install it with: pip install python-dotenv")


# Model Provider Configuration
MODEL_PROVIDERS = {
    # OpenAI Models
    'gpt4.5': {
        'provider': 'openai',
        'model_name': 'gpt-4.5-preview',
        'base_url': 'https://api.openai.com/v1/',
        'api_key_env': 'OPENAI_API_KEY',
    },
    'gpt4': {
        'provider': 'openai', 
        'model_name': 'gpt-4o-2024-08-06',
        'base_url': 'https://api.openai.com/v1/',
        'api_key_env': 'OPENAI_API_KEY',
    },
    # 'chatgpt': {
    #     'provider': 'openai',
    #     'model_name': 'gpt-3.5-turbo',
    #     'base_url': 'https://api.openai.com/v1/',
    #     'api_key_env': 'OPENAI_API_KEY',
    # },
    
    # Anthropic Models (Claude)
    'claude4': {
        'provider': 'anthropic',
        'model_name': 'claude-sonnet-4-20250514',
        'api_key_env': 'ANTHROPIC_API_KEY',
    },
    'claude4.5': {
        'provider': 'anthropic',
        'model_name': 'claude-sonnet-4-20250514',  
        'api_key_env': 'ANTHROPIC_API_KEY',
    },
    
    # Google Gemini Models
    'gemini-2.5-pro': {
        'provider': 'google',
        'model_name': 'gemini-2.5-pro-preview-06-05',
        'api_key_env': 'GEMINI_API_KEY',
    },
    'gemini-2.5-flash': {
        'provider': 'google',
        'model_name': 'gemini-2.5-flash-preview-05-20',
        'api_key_env': 'GEMINI_API_KEY',
    },
    
    'deepseek': {
        'provider': 'huggingface',
        'model_name': 'deepseek-ai/DeepSeek-V3',
        'api_key_env': 'HUGGINGFACE_API_KEY',
        'base_url': 'https://router.huggingface.co/v1/',
    },
}


def get_model_config(model_name: str) -> Dict[str, Any]:
    """Get configuration for a specific model."""
    if model_name not in MODEL_PROVIDERS:
        raise ValueError(f"Unknown model: {model_name}. Available models: {list(MODEL_PROVIDERS.keys())}")
    return MODEL_PROVIDERS[model_name]


def get_api_key(model_name: str) -> str:
    """Get API key for a specific model from environment variables."""
    config = get_model_config(model_name)
    api_key = os.getenv(config['api_key_env'])
    # print("t" , os.getenv("HUGGINGFACE_API_KEY"))
    # print("found" , api_key)
    if not api_key:
        raise ValueError(f"API key not found. Please set {config['api_key_env']} environment variable.")
    return api_key


def list_available_models() -> list:
    """List all available model names."""
    return list(MODEL_PROVIDERS.keys())


def get_provider(model_name: str) -> str:
    """Get the provider for a specific model."""
    return get_model_config(model_name)['provider']


# Default model capabilities for all providers
DEFAULT_MODEL_CAPABILITIES = {
    "vision": True,
    "function_calling": True,
    "json_output": True,
}


def create_model_client(model_name: str):
    """
    Factory function to create appropriate model client based on provider.
    
    Args:
        model_name: Name of the model (e.g., 'gpt4.5', 'claude4', 'gemini-2.5-pro', 'deepseek')
    
    Returns:
        Configured model client instance
    """
    config = get_model_config(model_name)
    provider = config['provider']
    api_key = get_api_key(model_name)
    
    if provider == 'openai':
        from autogen_ext.models.openai import OpenAIChatCompletionClient
        return OpenAIChatCompletionClient(
            model=config['model_name'],
            base_url=config.get('base_url', 'https://api.openai.com/v1/'),
            api_key=api_key,
            model_capabilities=DEFAULT_MODEL_CAPABILITIES,
        )
    
    elif provider == 'anthropic':
        try:
            from autogen_ext.models.anthropic import AnthropicChatCompletionClient
            return AnthropicChatCompletionClient(
                model=config['model_name'],
                api_key=api_key,
                model_capabilities=DEFAULT_MODEL_CAPABILITIES,
            )
        except ImportError:
            # Fallback to using OpenAI-compatible client for Anthropic
            from autogen_ext.models.openai import OpenAIChatCompletionClient
            return OpenAIChatCompletionClient(
                model=config['model_name'],
                base_url='https://api.anthropic.com/v1/',
                api_key=api_key,
                model_capabilities=DEFAULT_MODEL_CAPABILITIES,
            )
    
    elif provider == 'google':
        try:
            from autogen_ext.models.gemini import GoogleGeminiChatCompletionClient
            return GoogleGeminiChatCompletionClient(
                model=config['model_name'],
                api_key=api_key,
                model_capabilities=DEFAULT_MODEL_CAPABILITIES,
            )
        except ImportError:
            # Fallback to genai client wrapper
            from google import genai
            
            class GeminiClientWrapper:
                """Wrapper for Google GenAI SDK compatibility with AG2"""
                
                def __init__(self, model: str, api_key: str, **kwargs):
                    self._model_name = model
                    self._client = genai.Client(api_key=api_key)
                    self._model_capabilities = kwargs.get('model_capabilities', {})
                
                async def create(self, messages: list, **kwargs):
                    """Convert AG2 messages to Gemini format and call API"""
                    prompt = ""
                    for msg in messages:
                        if hasattr(msg, 'content'):
                            prompt += f"{msg.content}\n"
                        elif isinstance(msg, dict):
                            prompt += f"{msg.get('content', '')}\n"
                    
                    response = self._client.models.generate_content(
                        model=self._model_name,
                        contents=prompt.strip()
                    )
                    
                    return type('obj', (object,), {
                        'choices': [type('obj', (object,), {
                            'message': type('obj', (object,), {
                                'content': response.text
                            })()
                        })()]
                    })()
            
            return GeminiClientWrapper(
                model=config['model_name'],
                api_key=api_key,
                model_capabilities=DEFAULT_MODEL_CAPABILITIES,
            )
    
    elif provider == 'huggingface':
        from autogen_ext.models.openai import OpenAIChatCompletionClient
        return OpenAIChatCompletionClient(
            model=config['model_name'],
            base_url=config.get('base_url', 'https://api-inference.huggingface.co/v1/'),
            api_key=api_key,
            model_capabilities=DEFAULT_MODEL_CAPABILITIES,
        )
    
    else:
        raise ValueError(f"Unsupported provider: {provider}")



if __name__ == "__main__":
    # print_env_setup_instructions()
    print(f"\nAvailable models: {list_available_models()}")
