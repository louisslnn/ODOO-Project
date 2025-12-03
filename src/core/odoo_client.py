"""Odoo ERP client implementation using XML-RPC."""

from typing import List, Dict, Any, Optional
import xmlrpc.client
from .erp_client import ERPClient
from .config import Config


class OdooClient(ERPClient):
    """Concrete implementation of ERPClient for Odoo.
    
    Uses XML-RPC API to communicate with Odoo instances.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize Odoo client.
        
        Args:
            config: Optional configuration dict. If not provided, uses Config singleton.
        """
        if config is None:
            app_config = Config.get()
            erp_config = app_config.erp
        else:
            erp_config = config

        self.url = erp_config.get("url", "") if isinstance(erp_config, dict) else erp_config.url
        self.database = (
            erp_config.get("database", "") if isinstance(erp_config, dict) else erp_config.database
        )
        self.username = (
            erp_config.get("username", "")
            if isinstance(erp_config, dict)
            else erp_config.username
        )
        self.password = (
            erp_config.get("password", "")
            if isinstance(erp_config, dict)
            else erp_config.password
        )

        self.common = None
        self.models = None
        self.uid = None
        self._connected = False

    def connect(self) -> bool:
        """Establish connection to Odoo via XML-RPC."""
        try:
            # Connect to common endpoint
            self.common = xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/common")

            # Authenticate
            self.uid = self.common.authenticate(self.database, self.username, self.password, {})

            if not self.uid:
                self._connected = False
                return False

            # Connect to object endpoint
            self.models = xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/object")
            self._connected = True
            return True

        except Exception as e:
            print(f"Connection error: {e}")
            self._connected = False
            return False

    def disconnect(self) -> None:
        """Close connection to Odoo."""
        self._connected = False
        self.common = None
        self.models = None
        self.uid = None

    def is_connected(self) -> bool:
        """Check if connection is active."""
        return self._connected and self.uid is not None

    def _execute_kw(
        self, model: str, method: str, args: List = None, kwargs: Dict = None
    ) -> Any:
        """Helper method to execute Odoo API calls.
        
        Args:
            model: Odoo model name (e.g., 'account.move')
            method: Method to call (e.g., 'search_read', 'create')
            args: Positional arguments
            kwargs: Keyword arguments
            
        Returns:
            API response
        """
        if not self.is_connected():
            raise ConnectionError("Not connected to Odoo. Call connect() first.")

        args = args or []
        kwargs = kwargs or {}

        return self.models.execute_kw(self.database, self.uid, self.password, model, method, args, kwargs)

    def get_account_moves(
        self,
        domain: Optional[List] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Fetch accounting entries (account.move)."""
        kwargs = {"fields": ["name", "date", "ref", "state", "journal_id", "amount_total"]}
        
        if limit:
            kwargs["limit"] = limit
        if offset:
            kwargs["offset"] = offset

        domain = domain or []
        return self._execute_kw("account.move", "search_read", [domain], kwargs)

    def get_account_move_lines(
        self,
        domain: Optional[List] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Fetch accounting entry lines (account.move.line)."""
        kwargs = {
            "fields": [
                "id",
                "name",
                "date",
                "move_id",
                "account_id",
                "partner_id",
                "debit",
                "credit",
                "balance",
                "reconciled",
                "full_reconcile_id",
            ]
        }
        
        if limit:
            kwargs["limit"] = limit
        if offset:
            kwargs["offset"] = offset

        domain = domain or []
        return self._execute_kw("account.move.line", "search_read", [domain], kwargs)

    def create_account_move(self, move_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new accounting entry."""
        move_id = self._execute_kw("account.move", "create", [move_data])
        
        # Fetch the created move
        moves = self._execute_kw(
            "account.move",
            "read",
            [[move_id]],
            {"fields": ["name", "date", "ref", "state", "journal_id", "amount_total"]}
        )
        
        return moves[0] if moves else {}

    def validate_account_move(self, move_id: int) -> bool:
        """Validate (post) an accounting entry."""
        try:
            self._execute_kw("account.move", "action_post", [[move_id]])
            return True
        except Exception:
            return False

    def get_invoices(
        self,
        invoice_type: str = "all",
        domain: Optional[List] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Fetch invoices."""
        model = "account.move"
        
        if domain is None:
            domain = []
        
        if invoice_type == "customer":
            domain.append(["move_type", "in", ["out_invoice", "out_refund"]])
        elif invoice_type == "vendor":
            domain.append(["move_type", "in", ["in_invoice", "in_refund"]])

        kwargs = {
            "fields": [
                "name",
                "date",
                "partner_id",
                "amount_total",
                "amount_residual",
                "state",
                "move_type",
                "currency_id",
            ]
        }
        
        if limit:
            kwargs["limit"] = limit

        return self._execute_kw(model, "search_read", [domain], kwargs)

    def get_payments(
        self,
        domain: Optional[List] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Fetch payment records."""
        model = "account.payment"
        domain = domain or []
        
        kwargs = {
            "fields": [
                "name",
                "date",
                "partner_id",
                "amount",
                "payment_type",
                "state",
                "reconciled_invoice_ids",
            ]
        }
        
        if limit:
            kwargs["limit"] = limit

        return self._execute_kw(model, "search_read", [domain], kwargs)

    def get_bank_statements(
        self,
        domain: Optional[List] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Fetch bank statements."""
        model = "account.bank.statement"
        domain = domain or []
        
        kwargs = {"fields": ["name", "date", "balance_start", "balance_end", "line_ids"]}
        
        if limit:
            kwargs["limit"] = limit

        return self._execute_kw(model, "search_read", [domain], kwargs)

    def get_accounts(
        self,
        domain: Optional[List] = None
    ) -> List[Dict[str, Any]]:
        """Fetch chart of accounts."""
        model = "account.account"
        domain = domain or []
        
        kwargs = {
            "fields": [
                "name",
                "code",
                "account_type",
                "reconcile",
                "deprecated",
                "company_id",
            ]
        }

        return self._execute_kw(model, "search_read", [domain], kwargs)

    def get_journals(
        self,
        domain: Optional[List] = None
    ) -> List[Dict[str, Any]]:
        """Fetch accounting journals."""
        model = "account.journal"
        domain = domain or []
        
        kwargs = {
            "fields": [
                "name",
                "code",
                "type",
                "currency_id",
                "default_account_id",
                "company_id",
            ]
        }

        return self._execute_kw(model, "search_read", [domain], kwargs)

    def create_activity(self, model, res_id, summary, note, user_id=None):
        """Creates an activity (To-DO) within Odoo linked to a document.
        
        Args:
            model: Model name (e.g., 'product.product', 'account.move')
            res_id: ID of the record to link the activity to
            summary: Activity summary/title
            note: Activity note/description
            user_id: User ID to assign the activity to (defaults to current user)
            
        Returns:
            True if successful, False otherwise
        """
        if not self.is_connected():
            return False

        if user_id is None:
            user_id = self.uid 

        try:
            # Get the ir.model ID for the given model name
            # Odoo requires res_model_id (the ID of ir.model), not res_model (the string)
            model_records = self._execute_kw(
                'ir.model',
                'search_read',
                [[('model', '=', model)]],
                {'fields': ['id'], 'limit': 1}
            )
            
            if not model_records:
                print(f"❌ Error: Model '{model}' not found in Odoo")
                return False
            
            res_model_id = model_records[0]['id']

            activity_data = {
                'res_model_id': res_model_id,  # Required: ID of ir.model
                'res_id': res_id,               # ID of the record in that model
                'activity_type_id': 4,          # To-Do activity type
                'summary': summary,             
                'note': note,                   
                'user_id': user_id,             
            }

            self._execute_kw('mail.activity', 'create', [activity_data])
            return True
        except Exception as e:
            print(f"❌ Error in creating activity: {e}")
            return False

