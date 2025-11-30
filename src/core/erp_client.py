"""Abstract base class for ERP clients."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime


class ERPClient(ABC):
    """Abstract interface for ERP system connections.
    
    This adapter pattern allows the Finance Agent to work with different
    ERP systems (Odoo, NetSuite, SAP) through a unified interface.
    """

    @abstractmethod
    def connect(self) -> bool:
        """Establish connection to the ERP system.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Close connection to the ERP system."""
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        """Check if connection is active.
        
        Returns:
            bool: True if connected, False otherwise
        """
        pass

    # Accounting Entries Methods
    @abstractmethod
    def get_account_moves(
        self,
        domain: Optional[List] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Fetch accounting entries (journal entries).
        
        Args:
            domain: Filter criteria (ERP-specific format)
            limit: Maximum number of records to return
            offset: Number of records to skip
            
        Returns:
            List of accounting move dictionaries
        """
        pass

    @abstractmethod
    def get_account_move_lines(
        self,
        domain: Optional[List] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Fetch accounting entry lines.
        
        Args:
            domain: Filter criteria (ERP-specific format)
            limit: Maximum number of records to return
            offset: Number of records to skip
            
        Returns:
            List of accounting move line dictionaries
        """
        pass

    @abstractmethod
    def create_account_move(self, move_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new accounting entry.
        
        Args:
            move_data: Dictionary containing move fields
            
        Returns:
            Created move dictionary with ID
        """
        pass

    @abstractmethod
    def validate_account_move(self, move_id: int) -> bool:
        """Validate (post) an accounting entry.
        
        Args:
            move_id: ID of the move to validate
            
        Returns:
            True if successful, False otherwise
        """
        pass

    # Invoice Methods
    @abstractmethod
    def get_invoices(
        self,
        invoice_type: str = "all",  # 'customer', 'vendor', 'all'
        domain: Optional[List] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Fetch invoices.
        
        Args:
            invoice_type: Type of invoices to fetch
            domain: Filter criteria
            limit: Maximum number of records
            
        Returns:
            List of invoice dictionaries
        """
        pass

    # Payment Methods
    @abstractmethod
    def get_payments(
        self,
        domain: Optional[List] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Fetch payment records.
        
        Args:
            domain: Filter criteria
            limit: Maximum number of records
            
        Returns:
            List of payment dictionaries
        """
        pass

    @abstractmethod
    def get_bank_statements(
        self,
        domain: Optional[List] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Fetch bank statements.
        
        Args:
            domain: Filter criteria
            limit: Maximum number of records
            
        Returns:
            List of bank statement dictionaries
        """
        pass

    # Account Methods
    @abstractmethod
    def get_accounts(
        self,
        domain: Optional[List] = None
    ) -> List[Dict[str, Any]]:
        """Fetch chart of accounts.
        
        Args:
            domain: Filter criteria
            
        Returns:
            List of account dictionaries
        """
        pass

    # Journal Methods
    @abstractmethod
    def get_journals(
        self,
        domain: Optional[List] = None
    ) -> List[Dict[str, Any]]:
        """Fetch accounting journals.
        
        Args:
            domain: Filter criteria
            
        Returns:
            List of journal dictionaries
        """
        pass

