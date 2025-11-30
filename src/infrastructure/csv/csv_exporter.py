"""CSV Exporter Implementation - Infrastructure Layer"""
import csv
from pathlib import Path
from typing import List
from datetime import datetime
from ...domain.entities.invoice import Invoice
from ...domain.entities.client import Client
from ...domain.repositories.csv_repository import CSVRepository


class CSVExporter(CSVRepository):
    """CSV export implementation"""

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

        # Write CSV with UTF-8-BOM encoding
        with open(filepath, 'w', newline='', encoding='utf-8-sig') as csvfile:
            writer = csv.writer(csvfile, delimiter=client.csv_delimiter)
            writer.writerow(headers)

            for invoice in invoices:
                for item in invoice.items:
                    row = [
                        invoice.invoice_number,
                        item.product_name,
                        item.product_code,
                        item.unit_of_measure,
                        self._format_decimal(item.quantity, client),
                        self._format_decimal(item.unit_price, client),
                        invoice.invoice_date.strftime('%Y-%m-%d') if invoice.invoice_date else '',
                        invoice.payment_date.strftime('%Y-%m-%d') if invoice.payment_date else '',
                        invoice.buyer_nit,
                        invoice.buyer_name,
                        invoice.seller_nit,
                        invoice.seller_name,
                        invoice.principal_vc or '',
                        invoice.municipality,
                        self._format_decimal(item.tax_percentage, client, use_decimal_places=False),
                        item.description or '',
                        invoice.active or '',
                        invoice.invoice_active or '',
                        invoice.warehouse or '',
                        invoice.incentive or '',
                        self._format_decimal(item.quantity, client),  # Cantidad Original
                        invoice.currency
                    ]
                    writer.writerow(row)

        return str(filepath)

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
