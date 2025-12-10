"""CSV Exporter Implementation - Infrastructure Layer"""
import csv
from pathlib import Path
from typing import List, Optional
from datetime import datetime
from decimal import Decimal
from src.domain.entities.invoice import Invoice
from src.domain.entities.client import Client
from src.domain.repositories.csv_repository import CSVRepository
from src.infrastructure.database.sqlite_repository import SQLiteRepository


class CSVExporter(CSVRepository):
    """CSV export implementation"""

    def __init__(self):
        """Initialize CSV exporter with database repository for product lookup"""
        # Initialize database repository for Pulgarin products
        db_path = Path("data") / "app.db"
        self.db_repo = SQLiteRepository(str(db_path))

    def export_invoice(self, invoice: Invoice, client: Client, output_path: str) -> str:
        """Export single invoice to CSV"""
        return self.export_invoices([invoice], client, output_path)

    def export_invoices(self, invoices: List[Invoice], client: Client, output_path: str) -> str:
        """Export multiple invoices to CSV"""
        if not invoices:
            raise ValueError("No invoices to export")

        # Create output directory
        output_dir = Path(output_path)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Generate filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{client.id}_invoices_{timestamp}.csv"
        filepath = output_dir / filename

        # Check if this is Pulgarin client (needs product database lookup)
        is_pulgarin = client.id.lower() == 'pulgarin'

        # CSV headers (as specified in requirements)
        headers = [
            'N° Factura',
            'Nombre Producto',
            'Codigo Subyacente',
            'Unidad Medida en Kg,Un,Lt',
            'Cantidad',
            'Precio Unitario',
            'Fecha Factura',
            'Fecha Pago',
            'Nit Comprador',
            'Nombre Comprador',
            'Nit Vendedor',
            'Nombre Vendedor',
            'Principal V,C',
            'Municipio',
            'Iva',
            'Descripción',
            'Activa',
            'Factura Activa',
            'Bodega',
            'Incentivo',
            'Cantidad Original',
            'Moneda'
        ]

        # Add Pulgarin-specific columns for product database lookup
        if is_pulgarin:
            headers.extend(['Peso', 'U/M BD', 'Valor Total'])

        # Write CSV with UTF-8-BOM encoding
        with open(filepath, 'w', newline='', encoding='utf-8-sig') as csvfile:
            writer = csv.writer(csvfile, delimiter=client.csv_delimiter)
            writer.writerow(headers)

            for invoice in invoices:
                for item in invoice.items:
                    # For Pulgarin, calculate converted quantity and unit price
                    if is_pulgarin:
                        peso_str, um_bd, product = self._lookup_pulgarin_product(item)

                        # Calculate converted quantity and unit price
                        if product and peso_str:
                            try:
                                # Convert peso to Decimal (remove any non-numeric chars except . and ,)
                                peso_clean = peso_str.replace(',', '.')
                                peso_decimal = Decimal(peso_clean)

                                # Cantidad Convertida = Cantidad Original × Peso
                                cantidad_convertida = item.quantity * peso_decimal

                                # Precio Unitario = TaxableAmount (Valor sin IVA) ÷ Cantidad Convertida
                                # TaxableAmount es el valor base antes de impuestos (<cbc:TaxableAmount>)
                                valor_total = item.get_subtotal()  # Subtotal sin IVA
                                if cantidad_convertida > 0:
                                    precio_unitario = valor_total / cantidad_convertida
                                else:
                                    # Fallback to original if conversion fails
                                    cantidad_convertida = item.quantity
                                    precio_unitario = item.unit_price
                                    valor_total = item.get_subtotal()

                                # Format peso with client's decimal separator
                                peso_str = self._format_decimal(peso_decimal, client)
                            except (ValueError, Decimal.InvalidOperation):
                                # If conversion fails, use original values
                                cantidad_convertida = item.quantity
                                precio_unitario = item.unit_price
                                valor_total = item.get_subtotal()
                        else:
                            # Product not found or no peso, use original values
                            cantidad_convertida = item.quantity
                            precio_unitario = item.unit_price
                            valor_total = item.get_subtotal()
                            peso_str = ''
                            um_bd = ''
                    else:
                        # For non-Pulgarin clients, use original values
                        cantidad_convertida = item.quantity
                        precio_unitario = item.unit_price

                    row = [
                        invoice.invoice_number,
                        item.product_name,
                        item.subyacente_code,  # Código subyacente (SPN-1)
                        item.unit_of_measure,
                        self._format_decimal(cantidad_convertida, client),  # Cantidad Convertida for Pulgarin
                        self._format_decimal(precio_unitario, client),  # Precio Unitario recalculado for Pulgarin
                        invoice.invoice_date.strftime('%Y-%m-%d') if invoice.invoice_date else '',
                        invoice.payment_date.strftime('%Y-%m-%d') if invoice.payment_date else '',
                        invoice.buyer_nit,
                        invoice.buyer_name,
                        invoice.seller_nit,
                        invoice.seller_name,
                        invoice.principal_vc,  # V = Vendedor
                        invoice.municipality,
                        self._format_decimal(item.tax_percentage, client, use_decimal_places=False),
                        invoice.description or '',  # Nota de la factura
                        invoice.active,  # Siempre 1
                        invoice.invoice_active,  # Siempre 1
                        invoice.warehouse or '',
                        invoice.incentive or '',
                        self._format_decimal(item.quantity, client),  # Cantidad Original (sin conversión)
                        invoice.currency  # 1=COP, 2=USD, 3=EUR
                    ]

                    # Add Pulgarin-specific product data from database
                    if is_pulgarin:
                        valor_total_str = self._format_decimal(valor_total, client)
                        row.extend([peso_str, um_bd, valor_total_str])

                    writer.writerow(row)

        return str(filepath)

    def _lookup_pulgarin_product(self, item) -> tuple:
        """Lookup product in Pulgarin database and return (peso, um, product_dict)

        Args:
            item: InvoiceItem to lookup

        Returns:
            Tuple of (peso, um, product_dict) or ('', '', None) if not found
        """
        try:
            # Try to find product by code or description
            product = self.db_repo.find_product_by_code_or_description(
                codigo=item.product_code if item.product_code else None,
                descripcion=item.product_name
            )

            if product:
                return (product.get('peso', ''), product.get('um', ''), product)
            else:
                # Product not found in database
                return ('', '', None)

        except Exception as e:
            # In case of error, return empty values
            return ('', '', None)

    def _format_decimal(self, value, client: Client, use_decimal_places: bool = True) -> str:
        """Format decimal according to client configuration"""
        if value is None:
            return ''

        if use_decimal_places:
            # Format with specified decimal places
            format_str = f"{{:.{client.decimal_places}f}}"
            formatted = format_str.format(value)
        else:
            # Format as-is
            formatted = str(float(value))

        # Replace decimal separator
        if client.decimal_separator == ',':
            formatted = formatted.replace('.', ',')

        return formatted
