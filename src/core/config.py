"""Configuration management for the Finance Employee AI Agent."""

import os
import re
from decimal import Decimal
from pathlib import Path
from typing import Optional, Union
from pydantic import BaseModel, Field, field_validator
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


class UniversalInvoice(BaseModel):
    """Universal invoice model that abstracts ERP-specific invoice formats.
    
    This model ensures that ControlBot and other components can work with invoices
    regardless of whether they come from Odoo, SAP, NetSuite, or other ERP systems.
    """

    vendor_id: Union[str, int] = Field(..., description="Vendor identifier (can be string or integer)")
    amount: Decimal = Field(..., description="Invoice amount", gt=0)
    currency: str = Field(..., description="Currency code (ISO 4217 format, e.g., USD, EUR)")
    vat_number: str = Field(..., description="VAT/Tax identification number")
    status: str = Field(..., description="Invoice status (e.g., draft, posted, paid, cancelled)")

    @field_validator("vat_number")
    @classmethod
    def validate_vat_number(cls, v: str) -> str:
        """Validate VAT number format.
        
        Accepts common VAT number formats:
        - EU VAT: 2-letter country code + alphanumeric (e.g., FR12345678901, DE123456789)
        - US EIN: XX-XXXXXXX format
        - UK VAT: GB + numbers
        - General: alphanumeric with optional separators (hyphens, spaces)
        """
        if not v:
            raise ValueError("VAT number cannot be empty")
        
        # Remove common separators for validation
        cleaned = re.sub(r'[\s\-\.]', '', v.upper())
        
        # Check minimum length (most VAT numbers are at least 5 characters)
        if len(cleaned) < 5:
            raise ValueError(f"VAT number '{v}' is too short (minimum 5 characters after removing separators)")
        
        # Check for valid format patterns
        # EU VAT: 2 letters + 2-12 alphanumeric characters
        eu_vat_pattern = r'^[A-Z]{2}[A-Z0-9]{2,12}$'
        # US EIN: 2 digits + hyphen + 7 digits (after cleaning becomes 9 digits)
        us_ein_pattern = r'^\d{9}$'
        # General alphanumeric (at least 5 chars)
        general_pattern = r'^[A-Z0-9]{5,}$'
        
        if re.match(eu_vat_pattern, cleaned) or re.match(us_ein_pattern, cleaned) or re.match(general_pattern, cleaned):
            return v  # Return original value with separators preserved
        
        raise ValueError(
            f"VAT number '{v}' does not match expected format. "
            "Expected formats: EU VAT (e.g., FR12345678901), US EIN (e.g., 12-3456789), "
            "or general alphanumeric (minimum 5 characters)"
        )

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        """Validate currency code format (ISO 4217)."""
        if not v:
            raise ValueError("Currency cannot be empty")
        
        # ISO 4217 currency codes are 3 uppercase letters
        if not re.match(r'^[A-Z]{3}$', v.upper()):
            raise ValueError(f"Currency '{v}' must be a valid ISO 4217 code (3 uppercase letters)")
        
        return v.upper()

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v: Union[Decimal, float, str]) -> Decimal:
        """Validate and convert amount to Decimal."""
        if isinstance(v, str):
            try:
                v = Decimal(v)
            except (ValueError, TypeError):
                raise ValueError(f"Amount '{v}' cannot be converted to a number")
        elif isinstance(v, float):
            v = Decimal(str(v))
        elif not isinstance(v, Decimal):
            raise ValueError(f"Amount must be a number, got {type(v)}")
        
        if v <= 0:
            raise ValueError("Amount must be greater than zero")
        
        return v


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