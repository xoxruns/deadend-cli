import os
from pathlib import Path
from dotenv import load_dotenv


class Config:
    """
    Configuration class that loads environment variables from a .env file
    and provides easy access to them for use with LangChain or other applications.
    """
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
        # cls.db_host = os.getenv("DB_HOST")
        # cls.db_port = os.getenv("DB_PORT")
        # cls.db_user = os.getenv("DB_USER")
        # cls.db_password = os.getenv("DB_PASSWORD")
        # cls.db_name = os.getenv("DB_NAME")

        # zap proxy key
        cls.zap_api_key = os.getenv("ZAP_PROXY_API_KEY")
        
        # Application settings
        cls.app_env = os.getenv("APP_ENV", "development")
        cls.debug_mode = os.getenv("DEBUG_MODE", "false").lower() == "true"
        cls.log_level = os.getenv("LOG_LEVEL", "INFO")

    # @classmethod
    # def get(cls, key: str, default: Any = None) -> Any:
    #     """
    #     Get an environment variable by key.
        
    #     Args:
    #         key (str): The environment variable key.
    #         default (Any, optional): Default value if the key doesn't exist.
            
    #     Returns:
    #         Any: The value of the environment variable or the default.
    #     """
    #     return os.getenv(key, default)
    
    # @classmethod
    # def get_all(cls) -> Dict[str, str]:
    #     """
    #     Get all environment variables as a dictionary.
        
    #     Returns:
    #         Dict[str, str]: Dictionary of all environment variables.
    #     """
    #     return dict(os.environ)
    
    @classmethod
    def get_database_url(cls) -> str:
        """
        Construct a database URL from the database configuration.
        
        Returns:
            str: Database URL string.
        """
        if not all([cls.db_host, cls.db_user, cls.db_password, cls.db_name]):
            return ""
        
        port = f":{cls.db_port}" if cls.db_port else ""
        return f"postgresql://{cls.db_user}:{cls.db_password}@{cls.db_host}{port}/{cls.db_name}"