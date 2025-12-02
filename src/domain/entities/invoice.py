"""Invoice Entity - Domain Layer"""
from dataclasses import dataclass, field
from datetime import date
from typing import List, Optional
from .invoice_item import InvoiceItem


@dataclass
class Invoice:
    """Represents a complete invoice"""

    invoice_number: str
    invoice_date: date
    payment_date: Optional[date]
    seller_nit: str
    seller_name: str
    buyer_nit: str
    buyer_name: str
    municipality: str
    items: List[InvoiceItem] = field(default_factory=list)
    currency: str = "1"  # Default currency code
    active: Optional[str] = None
    invoice_active: Optional[str] = None
    warehouse: Optional[str] = None
    incentive: Optional[str] = None
    principal_vc: Optional[str] = None

    def add_item(self, item: InvoiceItem) -> None:
        """Add an item to the invoice"""
        self.items.append(item)

    def get_total_items(self) -> int:
        """Get total number of items"""
        return len(self.items)
