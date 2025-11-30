"""CSV Repository Interface - Domain Layer"""
from abc import ABC, abstractmethod
from typing import List
from ..entities.invoice import Invoice
from ..entities.client import Client


class CSVRepository(ABC):
    """Abstract interface for CSV export operations"""

    @abstractmethod
    def export_invoice(self, invoice: Invoice, client: Client,
                      output_path: str) -> str:
        """Export single invoice to CSV"""
        pass

    @abstractmethod
    def export_invoices(self, invoices: List[Invoice], client: Client,
                       output_path: str) -> str:
        """Export multiple invoices to CSV"""
        pass
