"""ControlBot: The Controller - Detects anomalies, compliance issues, and risk."""

from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum
from pydantic import BaseModel
from loguru import logger

from ...core.erp_client import ERPClient


class IssueSeverity(str, Enum):
    """Severity levels for control issues."""

    ERROR = "error"  # Must be fixed immediately
    WARNING = "warning"  # Should be reviewed
    INFO = "info"  # Informational


class ControlIssue(BaseModel):
    """Represents a control check issue."""

    check_name: str
    severity: IssueSeverity
    message: str
    entity_type: str  # e.g., "account.move.line", "account.move"
    entity_id: Optional[int] = None
    entity_name: Optional[str] = None
    details: Dict[str, Any] = {}
    detected_at: datetime = datetime.now()


class ControlBot:
    """The Controller - Detects anomalies, compliance issues, and risk.
    
    This bot performs various control checks on accounting data and generates
    a "Finance To-Do List" of issues that need human attention.
    """

    def __init__(self, erp_client: ERPClient):
        """Initialize ControlBot.
        
        Args:
            erp_client: Connected ERP client instance
        """
        self.erp_client = erp_client
        self.issues: List[ControlIssue] = []

    def run_all_checks(self) -> List[ControlIssue]:
        """Run all control checks and return issues.
        
        Returns:
            List of detected control issues
        """
        logger.info("Starting ControlBot checks...")
        self.issues = []

        # Basic Checks
        self.check_zero_amount_entries()
        self.check_unbalanced_journals()
        self.check_garbage_accounts()

        # Inventory Checks
        self.check_negative_stock()
        self.check_zero_cost_items()

        # VAT Checks
        self.check_vat_consistency()

        # Consistency Checks
        self.check_invoice_receipt_mismatch()

        logger.info(f"ControlBot completed. Found {len(self.issues)} issues.")
        return self.issues

    def check_zero_amount_entries(self) -> None:
        """Check for entries with zero amount (debit = credit = 0)."""
        logger.info("Running check: Zero amount entries")

        try:
            move_lines = self.erp_client.get_account_move_lines(
                domain=[["date", ">=", (datetime.now().replace(day=1)).strftime("%Y-%m-%d")]]
            )

            for line in move_lines:
                debit = float(line.get("debit", 0) or 0)
                credit = float(line.get("credit", 0) or 0)

                if debit == 0 and credit == 0:
                    issue = ControlIssue(
                        check_name="zero_amount_entry",
                        severity=IssueSeverity.WARNING,
                        message=f"Entry line has zero amount (debit=0, credit=0)",
                        entity_type="account.move.line",
                        entity_id=line.get("id"),
                        entity_name=line.get("name"),
                        details={
                            "move_id": line.get("move_id"),
                            "account_id": line.get("account_id"),
                            "date": line.get("date"),
                        },
                    )
                    self.issues.append(issue)

        except Exception as e:
            logger.error(f"Error in zero amount check: {e}")

    def check_unbalanced_journals(self) -> None:
        """Check that journals balance (sum of debits = sum of credits)."""
        logger.info("Running check: Unbalanced journals")

        try:
            # Get recent moves
            moves = self.erp_client.get_account_moves(
                domain=[["state", "=", "posted"]],
                limit=1000
            )

            # Get all lines for these moves
            move_ids = [move["id"] for move in moves]
            
            if not move_ids:
                return

            all_lines = self.erp_client.get_account_move_lines(
                domain=[["move_id", "in", move_ids]]
            )

            # Group lines by move_id
            lines_by_move: Dict[int, List[Dict]] = {}
            for line in all_lines:
                move_id = line.get("move_id")
                if isinstance(move_id, list):
                    move_id = move_id[0] if move_id else None
                
                if move_id:
                    if move_id not in lines_by_move:
                        lines_by_move[move_id] = []
                    lines_by_move[move_id].append(line)

            # Check balance for each move
            for move_id, lines in lines_by_move.items():
                total_debit = sum(float(line.get("debit", 0) or 0) for line in lines)
                total_credit = sum(float(line.get("credit", 0) or 0) for line in lines)
                
                # Allow small rounding differences (0.01)
                if abs(total_debit - total_credit) > 0.01:
                    move_name = next(
                        (m["name"] for m in moves if m["id"] == move_id),
                        f"Move #{move_id}"
                    )
                    
                    issue = ControlIssue(
                        check_name="unbalanced_journal",
                        severity=IssueSeverity.ERROR,
                        message=(
                            f"Journal entry is unbalanced: "
                            f"Total Debit={total_debit:.2f}, Total Credit={total_credit:.2f}, "
                            f"Difference={abs(total_debit - total_credit):.2f}"
                        ),
                        entity_type="account.move",
                        entity_id=move_id,
                        entity_name=move_name,
                        details={
                            "total_debit": total_debit,
                            "total_credit": total_credit,
                            "difference": abs(total_debit - total_credit),
                        },
                    )
                    self.issues.append(issue)

        except Exception as e:
            logger.error(f"Error in unbalanced journal check: {e}")

    def check_garbage_accounts(self) -> None:
        """Flag entries on 'garbage' or deprecated accounts."""
        logger.info("Running check: Garbage accounts")

        try:
            # Get deprecated accounts
            accounts = self.erp_client.get_accounts(
                domain=[["deprecated", "=", True]]
            )

            if not accounts:
                return

            deprecated_account_ids = [acc["id"] for acc in accounts]
            deprecated_account_names = {acc["id"]: acc["name"] for acc in accounts}

            # Get recent lines on these accounts
            move_lines = self.erp_client.get_account_move_lines(
                domain=[
                    ["account_id", "in", deprecated_account_ids],
                    ["date", ">=", (datetime.now().replace(day=1)).strftime("%Y-%m-%d")],
                ]
            )

            for line in move_lines:
                account_id = line.get("account_id")
                if isinstance(account_id, list):
                    account_id = account_id[0] if account_id else None

                if account_id and account_id in deprecated_account_names:
                    issue = ControlIssue(
                        check_name="garbage_account_usage",
                        severity=IssueSeverity.WARNING,
                        message=(
                            f"Entry found on deprecated account: "
                            f"{deprecated_account_names[account_id]}"
                        ),
                        entity_type="account.move.line",
                        entity_id=line.get("id"),
                        entity_name=line.get("name"),
                        details={
                            "account_id": account_id,
                            "account_name": deprecated_account_names[account_id],
                            "move_id": line.get("move_id"),
                        },
                    )
                    self.issues.append(issue)

        except Exception as e:
            logger.error(f"Error in garbage account check: {e}")

    def check_negative_stock(self) -> None:
        """Flag negative stock quantities."""
        logger.info("Running check: Negative stock")

        try:
            # This is a placeholder - actual implementation depends on ERP's inventory model
            # For Odoo, we would query product.product or stock.quant
            logger.warning("Negative stock check not yet implemented - requires inventory model access")
            
        except Exception as e:
            logger.error(f"Error in negative stock check: {e}")

    def check_zero_cost_items(self) -> None:
        """Flag items with Cost = 0."""
        logger.info("Running check: Zero cost items")

        try:
            # This is a placeholder - actual implementation depends on ERP's product/cost model
            logger.warning("Zero cost items check not yet implemented - requires product/cost model access")
            
        except Exception as e:
            logger.error(f"Error in zero cost check: {e}")

    def check_vat_consistency(self) -> None:
        """Validate correct VAT rate per country/operation."""
        logger.info("Running check: VAT consistency")

        try:
            # This is a placeholder - requires detailed VAT configuration
            logger.warning("VAT consistency check not yet fully implemented - requires VAT configuration")
            
        except Exception as e:
            logger.error(f"Error in VAT consistency check: {e}")

    def check_invoice_receipt_mismatch(self) -> None:
        """Alert if Invoice Amount > Receipt Amount."""
        logger.info("Running check: Invoice-Receipt mismatch")

        try:
            # Get vendor invoices
            invoices = self.erp_client.get_invoices(
                invoice_type="vendor",
                limit=500
            )

            for invoice in invoices:
                invoice_amount = float(invoice.get("amount_total", 0) or 0)
                
                # This is simplified - in reality, we'd need to match invoices to receipts
                # For now, we check if there's a residual amount that seems suspicious
                residual = float(invoice.get("amount_residual", 0) or 0)
                
                # If residual is greater than total, that's suspicious
                if residual > invoice_amount:
                    issue = ControlIssue(
                        check_name="invoice_receipt_mismatch",
                        severity=IssueSeverity.WARNING,
                        message=(
                            f"Invoice {invoice.get('name')} has residual amount "
                            f"({residual:.2f}) greater than total amount ({invoice_amount:.2f})"
                        ),
                        entity_type="account.move",
                        entity_id=invoice.get("id"),
                        entity_name=invoice.get("name"),
                        details={
                            "invoice_amount": invoice_amount,
                            "residual_amount": residual,
                            "partner_id": invoice.get("partner_id"),
                        },
                    )
                    self.issues.append(issue)

        except Exception as e:
            logger.error(f"Error in invoice-receipt mismatch check: {e}")

    def generate_todo_list(self) -> str:
        """Generate a human-readable Finance To-Do List.
        
        Returns:
            Formatted string with all issues organized by severity
        """
        if not self.issues:
            return "✓ No issues detected. All checks passed."

        output = ["=" * 60]
        output.append("FINANCE TO-DO LIST")
        output.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        output.append(f"Total Issues: {len(self.issues)}")
        output.append("=" * 60)
        output.append("")

        # Group by severity
        errors = [i for i in self.issues if i.severity == IssueSeverity.ERROR]
        warnings = [i for i in self.issues if i.severity == IssueSeverity.WARNING]
        infos = [i for i in self.issues if i.severity == IssueSeverity.INFO]

        if errors:
            output.append("🔴 ERRORS (Must Fix)")
            output.append("-" * 60)
            for idx, issue in enumerate(errors, 1):
                output.append(f"{idx}. [{issue.check_name}] {issue.message}")
                if issue.entity_name:
                    output.append(f"   Entity: {issue.entity_name} (ID: {issue.entity_id})")
                output.append("")

        if warnings:
            output.append("🟡 WARNINGS (Should Review)")
            output.append("-" * 60)
            for idx, issue in enumerate(warnings, 1):
                output.append(f"{idx}. [{issue.check_name}] {issue.message}")
                if issue.entity_name:
                    output.append(f"   Entity: {issue.entity_name} (ID: {issue.entity_id})")
                output.append("")

        if infos:
            output.append("ℹ️  INFO")
            output.append("-" * 60)
            for idx, issue in enumerate(infos, 1):
                output.append(f"{idx}. [{issue.check_name}] {issue.message}")
                output.append("")

        return "\n".join(output)

