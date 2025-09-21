import os
from pathlib import Path
from dotenv import load_dotenv
from pydantic_settings import BaseSettings


class ModelConfig(BaseSettings):
    api_key: str
    model_name: str
    base_url: str | None = None

class ModelSettings(BaseSettings):
      # Model provider configs
      openai: ModelConfig | None = None
      anthropic: ModelConfig | None = None
      gemini: ModelConfig | None = None
      # Default model to use
      default_provider: str = "openai"


class Config:
    """
    Configuration class that loads environment variables from a .env file or from 
    environment variables 
    """
    # Models 
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")
    openai_model_name : str | None = os.getenv("OPENAI_MODEL", "o4-mini-2025-04-16")
    anthropic_api_key: str | None = os.getenv("ANTHROPIC_API_KEY")
    anthropic_model_name : str | None = os.getenv("ANTHROPIC_MODEL")
    gemini_api_key: str | None = os.getenv("GEMINI_API_KEY")
    gemini_model_name : str | None = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    # Embedding model
    embedding_model: str | None  = os.getenv("EMBEDDING_MODEL")

    # Database
    db_url: str | None = os.getenv("DB_URL")
    
    # Tools
    zap_api_key: str | None = os.getenv("ZAP_PROXY_API_KEY")

    # Application settings
    app_env: str = os.getenv("APP_ENV", "development")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")

    @classmethod
    def configure(cls, env_file: str = ".env"):
        """
        Initialize the configuration by loading environment variables from the specified file.
        """
        cls.env_file = env_file

    @classmethod
    def _load_env_vars(cls) -> None:
        """Load environment variables from the .env file."""
        env_path = Path(cls.env_file)
        if not env_path.exists():
            raise FileNotFoundError(f"Environment file not found: {cls.env_file}")
        # Load the environment variables
        load_dotenv(dotenv_path=cls.env_file)

    @classmethod
    def get_models_settings(cls) -> ModelSettings:
        model_settings = ModelSettings()

        if cls.openai_api_key:
            model_settings.openai = ModelConfig(
                api_key=cls.openai_api_key,
                model_name=cls.openai_model_name if cls.openai_model_name else "gpt-4o"
            )
        
        if cls.anthropic_api_key:
            model_settings.anthropic = ModelConfig(
                api_key=cls.anthropic_api_key,
                model_name=cls.anthropic_model_name if cls.anthropic_model_name else "claude-3-5-sonnet-20241022"
            )

        if cls.gemini_api_key:
            model_settings.gemini = ModelConfig(
                api_key=cls.gemini_api_key,
                model_name=cls.gemini_model_name if cls.gemini_model_name else "gemini-2.5-flash",
                # base_url="https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"            
            )
        
        return model_settings