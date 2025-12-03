"""Main entry point for the Finance Employee AI Agent."""

import sys
from loguru import logger
from src.core.config import Config
from src.core.odoo_client import OdooClient
from src.bots.control.control_bot import ControlBot
from src.bots.reporting.report_bot import ReportBot
from src.bots.reporting.llm_bot import LLMBot

def setup_logging(log_level: str = "INFO"):
    logger.remove()
    logger.add(sys.stdout, format="<green>{time:HH:mm:ss}</green> | <level>{message}</level>", level=log_level)

def main():
    # --- SETUP ---
    config = Config.load()
    setup_logging(config.log_level)
    
    logger.info("🤖 AI Finance Agent - Starting...")

    # ERP Connection
    client = OdooClient()
    if not client.connect():
        logger.error("❌ ERP Connection Failed.")
        sys.exit(1)
    
    logger.success(f"✅ Connected to database: {config.erp.database}")

    # Instantiate Bots
    control_bot = ControlBot(client)
    report_bot = ReportBot(client)
    llm_bot = LLMBot()

    # --- INTERACTIVE LOOP ---
    print("\n" + "="*60)
    print("🧠 AI Mode Activated. Ask your questions in natural language.")
    print("Examples: 'What is the revenue this month?', 'Any risks detected?', 'Summarize the status'.")
    print("Type 'exit' to quit.")
    print("="*60 + "\n")

    while True:
        try:
            user_input = input("👤 You > ").strip()
            
            if user_input.lower() in ['exit', 'quit', 'bye']:
                print("🤖 Goodbye!")
                break
            
            if not user_input:
                continue

            # --- DATA RETRIEVAL ---
            print("   Thinking... (Analyzing Odoo data...)")
            
            # A. Get Revenue
            revenue = report_bot.get_monthly_revenue()
            
            # B. Get Anomalies (Audit)
            # We run checks but don't print the huge list, we pass it to context
            issues = control_bot.run_all_checks()
            issues_summary = control_bot.generate_todo_list()

            # C. Build Context for AI (In English)
            context = f"""
            - Current Database: {config.erp.database}
            - Monthly Revenue (Untaxed): {revenue:,.2f} €
            - Number of Anomalies Detected: {len(issues)}
            
            DETAILED AUDIT REPORT:
            {issues_summary}
            """

            # --- ASK GEMINI ---
            answer = llm_bot.ask_finance_advisor(user_input, context)
            
            print(f"\n🤖 Agent > {answer}\n")

        except KeyboardInterrupt:
            print("\n🤖 Forced Exit. Bye!")
            break
        except Exception as e:
            logger.error(f"Unexpected Error: {e}")

    client.disconnect()

if __name__ == "__main__":
    main()