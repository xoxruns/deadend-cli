from typing import Dict
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.providers.anthropic import AnthropicProvider
from pydantic_ai.providers.google import GoogleProvider

from core import Config

# AIModel abstraction
AIModel = OpenAIModel | AnthropicModel | GeminiModel

class ModelRegistry:
    def __init__(self, config: Config):
        self._models: Dict[str, AIModel] = {}
        self._initialize_models(config=config)

    def _initialize_models(self, config: Config):
        models_settings = config.get_models_settings()

        if models_settings.openai:
            openai_settings = models_settings.openai
            self._models['openai'] = OpenAIModel(
                model_name=openai_settings.model_name,
                provider=OpenAIProvider(api_key=openai_settings.api_key)
            )
        
        if models_settings.anthropic:
            anthropic_settings = models_settings.anthropic
            self._models['anthropic'] = AnthropicModel(
                model_name=anthropic_settings.model_name,
                provider=AnthropicProvider(api_key=anthropic_settings.api_key)
            )

        if models_settings.gemini:
            gemini_settings = models_settings.openai
            self._models['gemini'] = GeminiModel(
                model_name=gemini_settings.model_name,
                provider=GoogleProvider(api_key=gemini_settings.api_key)
            )
        
    def get_model(self, provider: str = 'openai') -> AIModel:
        if provider not in self._models:
            raise ValueError(f"Model provider {provider} not supported.")
        elif self._models == {}:
            raise ValueError("No model was instantiated. Have you tried supplying an API key for the Model?")
        return self._models[provider]
    
    def list_configured_providers(self) -> list[str]:
        return list(self._models.keys())
    
    # Evaluation
    def get_all_models(self) -> Dict[str, AIModel]:
        return self._models.copy()