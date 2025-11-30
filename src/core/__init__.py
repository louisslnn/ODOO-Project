"""Core module for ERP adapters and configuration."""

from .erp_client import ERPClient
from .odoo_client import OdooClient
from .config import Config

__all__ = ["ERPClient", "OdooClient", "Config"]

