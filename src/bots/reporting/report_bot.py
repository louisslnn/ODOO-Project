"""ReportBot: The Analyst - Generates KPIs and explains numbers."""

from datetime import datetime
from typing import Dict, Any
from loguru import logger
from ...core.erp_client import ERPClient

class ReportBot:
    def __init__(self, erp_client: ERPClient):
        self.erp_client = erp_client

    def get_monthly_revenue(self) -> float:
        """Calculate the current month's revenue (tax excluded)."""
        
        # 1. Define date range (from first of the month to today)
        today = datetime.now()
        start_of_month = today.replace(day=1).strftime("%Y-%m-%d")
        
        logger.info(f"📊 Calculating revenue since {start_of_month}...")

        # 2. Search criteria (Odoo Domain)
        # - Customer invoice (out_invoice)
        # - Posted (no drafts in real revenue)
        # - Date in the current month
        domain = [
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted'),
            ('date', '>=', start_of_month)
        ]

        try:
            # 3. Fetch invoices
            invoices = self.erp_client.get_invoices(
                invoice_type="customer",
                domain=domain,
                limit=1000  # Large upper bound
            )

            # 4. Compute total (Untaxed amount)
            total_revenue = sum(float(inv.get('amount_untaxed', 0) or 0) for inv in invoices)
            
            return total_revenue

        except Exception as e:
            logger.error(f"Error while computing revenue: {e}")
            return 0.0