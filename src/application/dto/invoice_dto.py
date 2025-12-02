"""Invoice Data Transfer Objects - Application Layer"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class InvoiceDTO:
    """DTO for invoice data transfer"""

    invoice_number: str
    invoice_date: str
    payment_date: Optional[str]
    seller_nit: str
    seller_name: str
    buyer_nit: str
    buyer_name: str
    municipality: str
    total_items: int
    output_file: Optional[str] = None
