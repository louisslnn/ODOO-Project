"""Example usage of the Finance Employee AI Agent.

This script demonstrates how to use the ControlBot independently.
"""

from src.core.config import Config
from src.core.odoo_client import OdooClient
from src.bots.control.control_bot import ControlBot
from loguru import logger

def example_controlbot():
    """Example: Run ControlBot checks."""
    
    # Load configuration
    config = Config.load()
    logger.info(f"Loaded configuration for ERP: {config.erp.type}")
    
    # Initialize ERP client
    erp_client = OdooClient()
    
    # Connect
    if not erp_client.connect():
        logger.error("Failed to connect to ERP")
        return
    
    logger.info("Connected successfully!")
    
    # Create ControlBot
    control_bot = ControlBot(erp_client)
    
    # Run checks
    logger.info("Running control checks...")
    issues = control_bot.run_all_checks()
    
    # Display results
    print("\n" + "="*60)
    print(f"Found {len(issues)} issues")
    print("="*60)
    
    # Generate todo list
    todo_list = control_bot.generate_todo_list()
    print(todo_list)
    
    # Disconnect
    erp_client.disconnect()
    logger.info("Disconnected from ERP")


if __name__ == "__main__":
    example_controlbot()

