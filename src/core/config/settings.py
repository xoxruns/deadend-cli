import os
from pathlib import Path
from dotenv import load_dotenv
from pydantic_settings import BaseSettings


class OpenAIConfig(BaseSettings):
    api_key: str
    model_name: str = "gpt-4o"

class AnthropicConfig(BaseSettings):
    api_key: str 
    model_name: str = "claude-3-5-sonnet-20241022"

class GeminiConfig(BaseSettings):
    api_key: str
    model_name: str = "gemini-1.5-pro"

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

    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")
    openai_model_name : str | None = os.getenv("OPENAI_MODEL") or "o4-mini-2025-04-16"
    anthropic_api_key: str | None = os.getenv("ANTHROPIC_API_KEY")
    anthropic_model_name : str | None = os.getenv("ANTHROPIC_MODEL")
    gemini_api_key: str | None = os.getenv("GEMINI_API_KEY")
    gemini_model_name : str | None = os.getenv("GEMINI_MODEL")

    @classmethod
    def configure(cls, env_file: str = ".env"):
        """
        Initialize the configuration by loading environment variables from the specified file.
        
        Args:
            env_file (str): Path to the .env file. Defaults to ".env" in the current directory.
        """
        cls.env_file = env_file
        # cls._load_env_vars()
        cls._load_env_vars_os()
        cls._initialize_common_configs()
    
    @classmethod
    def _load_env_vars(cls) -> None:
        """Load environment variables from the .env file."""
        env_path = Path(cls.env_file)
        if not env_path.exists():
            raise FileNotFoundError(f"Environment file not found: {cls.env_file}")
            
        # Load the environment variables
        load_dotenv(dotenv_path=cls.env_file)

    @classmethod
    def _load_env_vars_os(cls) -> None:
        cls.openai_api_key = os.environ["OPENAI_API_KEY"]
        cls.model_name = os.environ["OPENAI_MODEL"]
        cls.embedding_model = os.environ["EMBEDDING_MODEL"]
        cls.zap_api_key = os.environ["ZAP_PROXY_API_KEY"]
        cls.db_url = os.environ["DB_URL"]

    @classmethod
    def _initialize_common_configs(cls) -> None:
        """Initialize commonly used configuration values."""
        # API keys from model providers
        cls.openai_api_key = os.getenv("OPENAI_API_KEY")
        # cls.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        # cls.huggingface_api_key = os.getenv("HUGGINGFACE_API_KEY")
        cls.embedding_model = os.getenv("EMBEDDING_MODEL")
        
        # Database configurations
        cls.db_url = os.getenv("DB_URL")


        # zap proxy key
        cls.zap_api_key = os.getenv("ZAP_PROXY_API_KEY")
        
        # Application settings
        cls.app_env = os.getenv("APP_ENV", "development")
        cls.debug_mode = os.getenv("DEBUG_MODE", "false").lower() == "true"
        cls.log_level = os.getenv("LOG_LEVEL", "INFO")

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
            model_settings.anthropic = ModelConfig(
                api_key=cls.gemini_api_key,
                model_name=cls.gemini_model_name if cls.gemini_model_name else "claude-3-5-sonnet-20241022"
            )
            
        return model_settings