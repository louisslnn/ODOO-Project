"""Main entry point for the Finance Employee AI Agent."""

import sys
from pathlib import Path
from datetime import datetime
from loguru import logger
from typing import Optional

from .core.config import Config
from .core.odoo_client import OdooClient
from .bots.control.control_bot import ControlBot


def setup_logging(log_file: Optional[str] = None, log_level: str = "INFO") -> None:
    """Configure logging."""
    logger.remove()  # Remove default handler
    
    # Console handler
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
        level=log_level,
    )
    
    # File handler
    if log_file:
        logger.add(
            log_file,
            rotation="10 MB",
            retention="30 days",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function} - {message}",
            level=log_level,
        )


def main():
    """Main entry point."""
    # Load configuration
    config = Config.load()
    
    # Setup logging
    setup_logging(config.log_file, config.log_level)
    
    logger.info("=" * 60)
    logger.info("Finance Employee AI Agent - Starting")
    logger.info(f"Mode: {config.mode}")
    logger.info(f"ERP Type: {config.erp.type}")
    logger.info("=" * 60)
    
    # Initialize ERP client
    if config.erp.type.lower() == "odoo":
        erp_client = OdooClient()
    else:
        logger.error(f"Unsupported ERP type: {config.erp.type}")
        sys.exit(1)
    
    # Connect to ERP
    logger.info("Connecting to ERP...")
    if not erp_client.connect():
        logger.error("Failed to connect to ERP. Please check your configuration.")
        sys.exit(1)
    
    logger.info("✓ Connected to ERP successfully")
    
    # Run ControlBot (MVP)
    logger.info("\n" + "=" * 60)
    logger.info("Running ControlBot...")
    logger.info("=" * 60)
    
    control_bot = ControlBot(erp_client)
    issues = control_bot.run_all_checks()
    
    # Generate and display To-Do List
    todo_list = control_bot.generate_todo_list()
    print("\n" + todo_list + "\n")
    
    # Save to file
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    todo_file = Path("logs") / f"todo_list_{timestamp}.txt"
    todo_file.parent.mkdir(parents=True, exist_ok=True)
    todo_file.write_text(todo_list)
    logger.info(f"To-Do List saved to: {todo_file}")
    
    # Disconnect
    erp_client.disconnect()
    logger.info("Disconnected from ERP")
    
    # Exit with error code if critical issues found
    error_count = len([i for i in issues if i.severity.value == "error"])
    if error_count > 0:
        logger.warning(f"Found {error_count} critical errors. Exiting with code 1.")
        sys.exit(1)
    
    logger.info("Finance Employee AI Agent - Completed successfully")


if __name__ == "__main__":
    main()

