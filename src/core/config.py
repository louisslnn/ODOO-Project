"""Configuration management for the Finance Employee AI Agent."""

import os
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class ERPConfig(BaseModel):
    """ERP connection configuration."""

    type: str = Field(default="odoo", description="ERP type: odoo, netsuite, sap")
    url: str = Field(..., description="ERP base URL")
    database: Optional[str] = Field(default=None, description="Database name")
    username: str = Field(..., description="Username for authentication")
    password: str = Field(..., description="Password for authentication")
    api_key: Optional[str] = Field(default=None, description="API key if required")


class AppConfig(BaseModel):
    """Application configuration."""

    erp: ERPConfig
    mode: str = Field(default="assistant", description="Operating mode: assistant or auto")
    log_level: str = Field(default="INFO", description="Logging level")
    log_file: Optional[str] = Field(default="logs/finance_agent.log", description="Log file path")
    check_interval_hours: int = Field(default=24, description="Interval for periodic checks (hours)")


class Config:
    """Singleton configuration manager."""

    _instance: Optional["Config"] = None
    _config: Optional[AppConfig] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
        return cls._instance

    @classmethod
    def load(cls) -> AppConfig:
        """Load configuration from environment variables."""
        if cls._config is None:
            erp_config = ERPConfig(
                type=os.getenv("ERP_TYPE", "odoo"),
                url=os.getenv("ERP_URL", ""),
                database=os.getenv("ERP_DATABASE", ""),
                username=os.getenv("ERP_USERNAME", ""),
                password=os.getenv("ERP_PASSWORD", ""),
                api_key=os.getenv("ERP_API_KEY"),
            )

            cls._config = AppConfig(
                erp=erp_config,
                mode=os.getenv("APP_MODE", "assistant"),
                log_level=os.getenv("LOG_LEVEL", "INFO"),
                log_file=os.getenv("LOG_FILE", "logs/finance_agent.log"),
                check_interval_hours=int(os.getenv("CHECK_INTERVAL_HOURS", "24")),
            )

            # Create log directory if it doesn't exist
            if cls._config.log_file:
                log_path = Path(cls._config.log_file)
                log_path.parent.mkdir(parents=True, exist_ok=True)

        return cls._config

    @classmethod
    def get(cls) -> AppConfig:
        """Get current configuration."""
        if cls._config is None:
            return cls.load()
        return cls._config

