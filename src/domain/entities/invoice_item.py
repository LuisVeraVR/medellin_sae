"""Invoice Item Entity - Domain Layer"""
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional


@dataclass
class InvoiceItem:
    """Represents a single item in an invoice"""

    product_name: str
    product_code: str
    subyacente_code: str  # Código subyacente (ej: SPN-1)
    quantity: Decimal
    unit_of_measure: str
    unit_price: Decimal
    tax_percentage: Decimal
    description: Optional[str] = None
    weight: Optional[Decimal] = None  # Peso del producto (PESO)

    @property
    def total_value(self) -> Decimal:
        """Calculate total value (quantity * unit_price) - valor total"""
        return self.quantity * self.unit_price

    def get_subtotal(self) -> Decimal:
        """Calculate subtotal without tax"""
        return self.quantity * self.unit_price

    def get_tax_amount(self) -> Decimal:
        """Calculate tax amount"""
        return self.get_subtotal() * (self.tax_percentage / Decimal('100'))

    def get_total(self) -> Decimal:
        """Calculate total including tax"""
        return self.get_subtotal() + self.get_tax_amount()
