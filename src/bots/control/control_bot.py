"""ControlBot: The Controller - Detects anomalies, compliance issues, and risk."""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from enum import Enum
from pydantic import BaseModel
from loguru import logger

from ...core.erp_client import ERPClient


class IssueSeverity(str, Enum):
    """Severity levels for control issues."""
    ERROR = "error"     # Must be fixed immediately -> Creates Odoo Activity
    WARNING = "warning" # Should be reviewed -> Creates Odoo Activity
    INFO = "info"       # Informational -> No Odoo Activity needed


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
    """The Controller - Detects anomalies and creates tasks in Odoo."""

    def __init__(self, erp_client: ERPClient):
        """Initialize ControlBot.
        
        Args:
            erp_client: Connected ERP client instance
        """
        self.erp_client = erp_client
        self.issues: List[ControlIssue] = []

    def _register_issue(self, issue: ControlIssue) -> None:
        """Helper to store the issue AND create an Odoo activity if needed."""
        
        # 1. Add to local list for reporting
        self.issues.append(issue)

        # 2. Create Odoo Activity for ERRORS and WARNINGS
        # We don't want to spam Odoo with simple INFO logs
        if issue.severity in [IssueSeverity.ERROR, IssueSeverity.WARNING]:
            if issue.entity_id and issue.entity_type:
                logger.info(f"⚡ Creating Odoo Activity for: {issue.message}")
                
                self.erp_client.create_activity(
                    model=issue.entity_type,
                    res_id=issue.entity_id,
                    summary=f"🤖 AI Audit: {issue.check_name}",
                    note=f"<p><b>Issue detected by Finance AI Agent:</b><br/>{issue.message}</p>"
                )

    def run_all_checks(self) -> List[ControlIssue]:
        """Run all control checks and return issues."""
        logger.info("Starting ControlBot checks...")
        self.issues = []

        # Basic Checks
        self.check_zero_amount_entries()
        self.check_unbalanced_journals()
        self.check_garbage_accounts()

        # Inventory Checks
        self.check_negative_stock()
        self.check_zero_cost_items()

        # VAT & Consistency Checks
        self.check_vat_consistency()
        self.check_invoice_receipt_mismatch()
        self.check_po_invoice_mismatch()

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
                    self._register_issue(ControlIssue(
                        check_name="zero_amount_entry",
                        severity=IssueSeverity.WARNING,
                        message=f"Entry line has zero amount (debit=0, credit=0)",
                        entity_type="account.move.line",
                        entity_id=line.get("id"),
                        entity_name=line.get("name"),
                        details={"move_id": line.get("move_id")}
                    ))

        except Exception as e:
            logger.error(f"Error in zero amount check: {e}")

    def check_unbalanced_journals(self) -> None:
        """Check that journals balance (sum of debits = sum of credits)."""
        logger.info("Running check: Unbalanced journals")

        try:
            moves = self.erp_client.get_account_moves(
                domain=[["state", "=", "posted"]],
                limit=100
            )
            move_ids = [move["id"] for move in moves]
            if not move_ids: return

            all_lines = self.erp_client.get_account_move_lines(domain=[["move_id", "in", move_ids]])
            
            # Helper dict to group lines
            lines_by_move: Dict[int, List[Dict]] = {}
            for line in all_lines:
                mid = line.get("move_id")[0] if isinstance(line.get("move_id"), list) else line.get("move_id")
                if mid:
                    lines_by_move.setdefault(mid, []).append(line)

            for move_id, lines in lines_by_move.items():
                total_debit = sum(float(l.get("debit", 0)) for l in lines)
                total_credit = sum(float(l.get("credit", 0)) for l in lines)
                
                if abs(total_debit - total_credit) > 0.01:
                    move_name = next((m["name"] for m in moves if m["id"] == move_id), f"#{move_id}")
                    
                    self._register_issue(ControlIssue(
                        check_name="unbalanced_journal",
                        severity=IssueSeverity.ERROR,
                        message=f"Unbalanced Journal: Debit={total_debit:.2f}, Credit={total_credit:.2f}",
                        entity_type="account.move",
                        entity_id=move_id,
                        entity_name=move_name,
                        details={"diff": abs(total_debit - total_credit)}
                    ))

        except Exception as e:
            logger.error(f"Error in unbalanced journal check: {e}")

    def check_garbage_accounts(self) -> None:
        """Flag entries on 'garbage' or deprecated accounts."""
        logger.info("Running check: Garbage accounts")

        try:
            # 1. Get deprecated accounts
            deprecated_accounts = self.erp_client._execute_kw(
                'account.account', 'search_read',
                [[('deprecated', '=', True)]], {'fields': ['name', 'code']}
            )
            if not deprecated_accounts: return

            deprecated_ids = [acc['id'] for acc in deprecated_accounts]
            acc_map = {acc['id']: f"{acc['code']} {acc['name']}" for acc in deprecated_accounts}

            # 2. Check usage in recent lines
            start_of_month = datetime.now().replace(day=1).strftime("%Y-%m-%d")
            lines = self.erp_client._execute_kw(
                'account.move.line', 'search_read',
                [[('account_id', 'in', deprecated_ids), ('date', '>=', start_of_month)]],
                {'fields': ['name', 'account_id', 'date'], 'limit': 50}
            )

            for line in lines:
                acc_id = line['account_id'][0]
                self._register_issue(ControlIssue(
                    check_name="garbage_account_usage",
                    severity=IssueSeverity.WARNING,
                    message=f"Usage of deprecated account ({acc_map.get(acc_id)}) detected.",
                    entity_type="account.move.line",
                    entity_id=line['id'],
                    entity_name=line['name'],
                    details={"account": acc_map.get(acc_id)}
                ))

        except Exception as e:
            logger.error(f"Error in garbage account check: {e}")

    def check_negative_stock(self) -> None:
        """Flag negative stock quantities."""
        logger.info("Running check: Negative stock")

        try:
            products = self.erp_client._execute_kw(
                'product.product', 'search_read',
                [[('detailed_type', '=', 'product'), ('qty_available', '<', 0)]],
                {'fields': ['name', 'default_code', 'qty_available'], 'limit': 100}
            )

            for product in products:
                self._register_issue(ControlIssue(
                    check_name="negative_stock",
                    severity=IssueSeverity.ERROR,
                    message=f"Critical negative stock: {product['qty_available']} units",
                    entity_type="product.product",
                    entity_id=product['id'],
                    entity_name=product['name'],
                    details={"qty": product.get('qty_available')}
                ))

        except Exception as e:
            logger.error(f"Error in negative stock check: {e}")

    def check_zero_cost_items(self) -> None:
        """Flag items with Cost = 0."""
        logger.info("Running check: Zero cost items")

        try:
            products = self.erp_client._execute_kw(
                'product.product', 'search_read',
                [[('detailed_type', '=', 'product'), ('standard_price', '=', 0.0), ('active', '=', True)]],
                {'fields': ['name', 'default_code'], 'limit': 100}
            )

            for product in products:
                self._register_issue(ControlIssue(
                    check_name="zero_cost_item",
                    severity=IssueSeverity.WARNING,
                    message=f"Product '{product['name']}' has a cost of 0.00. Check Margin!",
                    entity_type="product.product",
                    entity_id=product['id'],
                    entity_name=product['name']
                ))

        except Exception as e:
            logger.error(f"Error in zero cost check: {e}")

    def check_vat_consistency(self) -> None:
        """Flag Customer Invoices with 0.00 Tax."""
        logger.info("Running check: VAT consistency")

        try:
            invoices = self.erp_client.get_invoices(
                invoice_type="customer",
                domain=[('state', '=', 'posted'), ('amount_untaxed', '>', 0), ('amount_tax', '=', 0)],
                limit=50
            )

            for inv in invoices:
                self._register_issue(ControlIssue(
                    check_name="suspicious_zero_vat",
                    severity=IssueSeverity.WARNING,
                    message=f"Customer Invoice {inv['name']} has 0.00 tax. Verify export status.",
                    entity_type="account.move",
                    entity_id=inv['id'],
                    entity_name=inv['name']
                ))

        except Exception as e:
            logger.error(f"Error in VAT consistency check: {e}")

    def check_invoice_receipt_mismatch(self) -> None:
        """Alert if Invoice Residual > Total (Suspicious)."""
        logger.info("Running check: Invoice-Receipt mismatch")

        try:
            invoices = self.erp_client.get_invoices(invoice_type="vendor", limit=100)

            for invoice in invoices:
                total = float(invoice.get("amount_total", 0) or 0)
                residual = float(invoice.get("amount_residual", 0) or 0)
                
                if residual > total:
                    self._register_issue(ControlIssue(
                        check_name="invoice_receipt_mismatch",
                        severity=IssueSeverity.WARNING,
                        message=f"Invoice residual ({residual}) is greater than total ({total}).",
                        entity_type="account.move",
                        entity_id=invoice.get("id"),
                        entity_name=invoice.get("name")
                    ))

        except Exception as e:
            logger.error(f"Error in mismatch check: {e}")

    def check_po_invoice_mismatch(self) -> None:
        """Check consistency between Purchase Orders and Vendor Bills.
        
        Detects if the invoiced amount is greater than the ordered amount,
        or if there's a significant price deviation.
        """
        logger.info("Running check: PO-Invoice mismatch")
        
        try:
            # Calculate date 30 days ago
            date_30_days_ago = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
            
            # 1. Get recent vendor invoices (last 30 days)
            invoices = self.erp_client._execute_kw(
                'account.move', 'search_read',
                [[
                    ('move_type', '=', 'in_invoice'),
                    ('state', 'in', ['posted', 'draft']),
                    ('date', '>=', date_30_days_ago)
                ]],
                {'fields': ['name', 'invoice_origin', 'amount_total', 'partner_id'], 'limit': 200}
            )
            
            if not invoices:
                return
            
            # 2. Process each invoice
            for invoice in invoices:
                invoice_origin = invoice.get('invoice_origin', '').strip()
                
                # Skip if no origin or multiple origins (e.g., "P001, P002")
                if not invoice_origin or ',' in invoice_origin:
                    if invoice_origin and ',' in invoice_origin:
                        logger.warning(f"Invoice {invoice['name']} has multiple origins: {invoice_origin}. Skipping.")
                    continue
                
                invoice_amount = float(invoice.get('amount_total', 0) or 0)
                
                # Skip if invoice amount is zero
                if invoice_amount == 0:
                    continue
                
                # 3. Find the Purchase Order by name
                try:
                    pos = self.erp_client._execute_kw(
                        'purchase.order', 'search_read',
                        [[('name', '=', invoice_origin)]],
                        {'fields': ['name', 'amount_total', 'state'], 'limit': 1}
                    )
                    
                    if not pos:
                        # PO not found - log but don't create an issue (could be manual invoice)
                        logger.debug(f"PO '{invoice_origin}' not found for invoice {invoice['name']}")
                        continue
                    
                    po = pos[0]
                    po_amount = float(po.get('amount_total', 0) or 0)
                    
                    # Skip if PO amount is zero
                    if po_amount == 0:
                        continue
                    
                    # 4. Compare amounts with tolerance of 1.00
                    difference = invoice_amount - po_amount
                    tolerance = 1.00
                    
                    # Check if invoice exceeds PO (with tolerance)
                    if difference > tolerance:
                        # Calculate percentage deviation
                        deviation_pct = (difference / po_amount) * 100 if po_amount > 0 else 0
                        
                        # Determine severity
                        if deviation_pct > 5 or difference > po_amount * 0.05:
                            severity = IssueSeverity.ERROR
                        else:
                            severity = IssueSeverity.WARNING
                        
                        # Create issue
                        self._register_issue(ControlIssue(
                            check_name="po_invoice_mismatch",
                            severity=severity,
                            message=(
                                f"Invoice {invoice['name']} ({invoice_amount:.2f}€) exceeds "
                                f"PO {po['name']} ({po_amount:.2f}€) by {difference:.2f}€ "
                                f"({deviation_pct:.1f}% deviation)"
                            ),
                            entity_type="account.move",
                            entity_id=invoice['id'],
                            entity_name=invoice['name'],
                            details={
                                "po_name": po['name'],
                                "po_amount": po_amount,
                                "invoice_amount": invoice_amount,
                                "difference": difference,
                                "deviation_pct": deviation_pct
                            }
                        ))
                
                except Exception as e:
                    logger.warning(f"Error processing invoice {invoice['name']} with origin {invoice_origin}: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Error in PO-Invoice mismatch check: {e}")

    def generate_todo_list(self) -> str:
        """Generate human-readable report."""
        if not self.issues:
            return "✓ No issues detected."

        output = [f"FINANCE TO-DO LIST ({len(self.issues)} issues)"]
        output.append("=" * 40)
        
        for issue in self.issues:
            icon = "🔴" if issue.severity == IssueSeverity.ERROR else "🟡" if issue.severity == IssueSeverity.WARNING else "ℹ️"
            output.append(f"{icon} [{issue.check_name}] {issue.message}")
            
        return "\n".join(output)