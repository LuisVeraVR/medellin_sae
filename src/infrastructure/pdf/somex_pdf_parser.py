"""Somex PDF Parser - Infrastructure Layer"""
import logging
import re
from typing import Dict, Any, Optional, List
from decimal import Decimal
import pdfplumber
import io


class SomexPDFParser:
    """Parser for Somex invoice PDFs"""

    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize PDF parser

        Args:
            logger: Logger instance
        """
        self.logger = logger or logging.getLogger(__name__)

    def parse_invoice_pdf(self, pdf_content: bytes) -> Optional[Dict[str, Any]]:
        """
        Parse Somex invoice PDF and extract required data

        Args:
            pdf_content: PDF file content as bytes

        Returns:
            Dictionary with invoice data matching XML parser structure
        """
        try:
            self.logger.info(f"Parsing PDF content ({len(pdf_content)} bytes)")

            # Open PDF from bytes
            with pdfplumber.open(io.BytesIO(pdf_content)) as pdf:
                if len(pdf.pages) == 0:
                    self.logger.error("PDF has no pages")
                    return None

                # Extract text from all pages
                full_text = ""
                for page in pdf.pages:
                    full_text += page.extract_text() + "\n"

                self.logger.debug(f"Extracted text length: {len(full_text)} chars")

                # Parse header information
                invoice_number = self._extract_invoice_number(full_text)
                invoice_date = self._extract_invoice_date(full_text)
                payment_date = self._extract_payment_date(full_text)
                buyer_nit = self._extract_buyer_nit(full_text)
                buyer_name = self._extract_buyer_name(full_text)
                municipality = self._extract_municipality(full_text)

                self.logger.info(
                    f"Header extracted: Invoice={invoice_number}, "
                    f"Date={invoice_date}, Buyer={buyer_nit}"
                )

                # Extract product table from first page
                items = self._extract_product_table(pdf.pages[0])

                if not items:
                    self.logger.warning("No items found in PDF table")

                # Create invoice data structure matching XML parser
                invoice_data = {
                    'invoice_number': invoice_number,
                    'invoice_date': invoice_date,
                    'payment_date': payment_date,
                    'buyer_nit': buyer_nit,
                    'buyer_name': buyer_name,
                    'seller_nit': '800221724',  # Fijo para Somex
                    'seller_name': 'PRODUCTORA DE INSUMOS AGROPECUARIOS SOMEX S.A.S',
                    'municipality': municipality,
                    'items': items
                }

                self.logger.info(
                    f"Parsed PDF invoice {invoice_number} with {len(items)} items"
                )

                return invoice_data

        except Exception as e:
            self.logger.error(f"Error parsing PDF: {e}", exc_info=True)
            return None

    def _extract_invoice_number(self, text: str) -> str:
        """
        Extract invoice number from PDF text
        Pattern: "FACTURA ELECTRÓNICA DE VENTA No." followed by number

        Args:
            text: Full PDF text

        Returns:
            Invoice number (e.g., "2B-286000")
        """
        try:
            # Look for pattern: "FACTURA ELECTRÓNICA DE VENTA No." followed by number
            patterns = [
                r'FACTURA\s+ELECTR[OÓ]NICA\s+DE\s+VENTA\s+No\.?\s*[:.]?\s*([A-Z0-9\-]+)',
                r'No\.?\s*Factura\s*[:.]?\s*([A-Z0-9\-]+)',
                r'N[°º]\s*Factura\s*[:.]?\s*([A-Z0-9\-]+)',
            ]

            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    invoice_number = match.group(1).strip()
                    self.logger.debug(f"Found invoice number: {invoice_number}")
                    return invoice_number

            self.logger.warning("Invoice number not found in PDF")
            return ""

        except Exception as e:
            self.logger.error(f"Error extracting invoice number: {e}")
            return ""

    def _extract_invoice_date(self, text: str) -> str:
        """
        Extract invoice date from PDF text
        Pattern: "Fecha Factura" or "Fecha de Factura" followed by date

        Args:
            text: Full PDF text

        Returns:
            Date in YYYY-MM-DD format
        """
        try:
            # Look for pattern: "Fecha Factura" or similar
            patterns = [
                r'Fecha\s+(?:de\s+)?Factura\s*[:.]?\s*(\d{4}-\d{2}-\d{2})',
                r'Fecha\s+(?:de\s+)?Factura\s*[:.]?\s*(\d{2})/(\d{2})/(\d{4})',
                r'Fecha\s+(?:de\s+)?Factura\s*[:.]?\s*(\d{2})-(\d{2})-(\d{4})',
            ]

            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    if len(match.groups()) == 1:
                        # Format: YYYY-MM-DD
                        date = match.group(1).strip()
                    else:
                        # Format: DD/MM/YYYY or DD-MM-YYYY
                        day, month, year = match.group(1), match.group(2), match.group(3)
                        date = f"{year}-{month}-{day}"

                    self.logger.debug(f"Found invoice date: {date}")
                    return date

            self.logger.warning("Invoice date not found in PDF")
            return ""

        except Exception as e:
            self.logger.error(f"Error extracting invoice date: {e}")
            return ""

    def _extract_payment_date(self, text: str) -> str:
        """
        Extract payment due date from PDF text
        Pattern: "Fecha Vencimiento" followed by date

        Args:
            text: Full PDF text

        Returns:
            Date in YYYY-MM-DD format
        """
        try:
            # Look for pattern: "Fecha Vencimiento" or similar
            patterns = [
                r'Fecha\s+(?:de\s+)?Vencimiento\s*[:.]?\s*(\d{4}-\d{2}-\d{2})',
                r'Fecha\s+(?:de\s+)?Vencimiento\s*[:.]?\s*(\d{2})/(\d{2})/(\d{4})',
                r'Fecha\s+(?:de\s+)?Vencimiento\s*[:.]?\s*(\d{2})-(\d{2})-(\d{4})',
                r'Vencimiento\s*[:.]?\s*(\d{4}-\d{2}-\d{2})',
            ]

            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    if len(match.groups()) == 1:
                        # Format: YYYY-MM-DD
                        date = match.group(1).strip()
                    else:
                        # Format: DD/MM/YYYY or DD-MM-YYYY
                        day, month, year = match.group(1), match.group(2), match.group(3)
                        date = f"{year}-{month}-{day}"

                    self.logger.debug(f"Found payment date: {date}")
                    return date

            self.logger.warning("Payment date not found in PDF")
            return ""

        except Exception as e:
            self.logger.error(f"Error extracting payment date: {e}")
            return ""

    def _extract_buyer_nit(self, text: str) -> str:
        """
        Extract buyer NIT from PDF text
        Pattern: "Nit:" or "NIT:" followed by number

        Args:
            text: Full PDF text

        Returns:
            Buyer NIT
        """
        try:
            # Look for pattern: "Nit:" or "NIT:"
            patterns = [
                r'Nit\s*[:.]?\s*(\d+)',
                r'NIT\s*[:.]?\s*(\d+)',
                r'(?:Cliente\s+)?NIT\s*[:.]?\s*(\d+)',
            ]

            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    nit = match.group(1).strip()
                    self.logger.debug(f"Found buyer NIT: {nit}")
                    return nit

            self.logger.warning("Buyer NIT not found in PDF")
            return ""

        except Exception as e:
            self.logger.error(f"Error extracting buyer NIT: {e}")
            return ""

    def _extract_buyer_name(self, text: str) -> str:
        """
        Extract buyer name from PDF text
        Pattern: "Cliente:" followed by name

        Args:
            text: Full PDF text

        Returns:
            Buyer name
        """
        try:
            # Look for pattern: "Cliente:" followed by name
            patterns = [
                r'Cliente\s*[:.]?\s*([A-ZÀ-Ÿ][A-ZÀ-Ÿ\s\.]+?)(?:\s+Nit|\s+NIT|\s+Ciudad|$)',
                r'Nombre\s+(?:del\s+)?Cliente\s*[:.]?\s*([A-ZÀ-Ÿ][A-ZÀ-Ÿ\s\.]+?)(?:\s+Nit|\s+NIT|\s+Ciudad|$)',
            ]

            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    name = match.group(1).strip()
                    self.logger.debug(f"Found buyer name: {name}")
                    return name

            self.logger.warning("Buyer name not found in PDF")
            return ""

        except Exception as e:
            self.logger.error(f"Error extracting buyer name: {e}")
            return ""

    def _extract_municipality(self, text: str) -> str:
        """
        Extract municipality from PDF text
        Pattern: "Ciudad-Dpto:" or similar

        Args:
            text: Full PDF text

        Returns:
            Municipality name
        """
        try:
            # Look for pattern: "Ciudad-Dpto:" or similar
            patterns = [
                r'Ciudad-Dpto\s*[:.]?\s*([A-ZÀ-Ÿ][A-ZÀ-Ÿ\s\-]+?)(?:\s+Tel|\s+Direcci[oó]n|\s+Fecha|$)',
                r'Ciudad\s*[:.]?\s*([A-ZÀ-Ÿ][A-ZÀ-Ÿ\s\-]+?)(?:\s+Tel|\s+Direcci[oó]n|\s+Fecha|$)',
                r'Municipio\s*[:.]?\s*([A-ZÀ-Ÿ][A-ZÀ-Ÿ\s\-]+?)(?:\s+Tel|\s+Direcci[oó]n|\s+Fecha|$)',
            ]

            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    municipality = match.group(1).strip()
                    self.logger.debug(f"Found municipality: {municipality}")
                    return municipality

            self.logger.warning("Municipality not found in PDF")
            return ""

        except Exception as e:
            self.logger.error(f"Error extracting municipality: {e}")
            return ""

    def _parse_colombian_number(self, value_str: str) -> Decimal:
        """
        Parse Colombian number format to Decimal
        Format: $ 9.778.875 or $ 9,778,875 or 9.778.875,00

        Args:
            value_str: Number string in Colombian format

        Returns:
            Decimal value
        """
        try:
            if not value_str:
                return Decimal('0')

            # Remove currency symbol and spaces
            cleaned = value_str.strip().replace('$', '').replace(' ', '').strip()

            if not cleaned:
                return Decimal('0')

            # Determine decimal separator
            # Colombian format typically uses comma for decimals and dot for thousands
            # But sometimes it's the opposite, so we need to be smart about it

            # Count dots and commas
            dot_count = cleaned.count('.')
            comma_count = cleaned.count(',')

            if comma_count == 0 and dot_count == 0:
                # No separators, just a plain number
                return Decimal(cleaned)

            elif comma_count > 0 and dot_count == 0:
                # Only commas - could be decimal separator or thousands separator
                # If there's only one comma and it's near the end (last 3 chars), it's decimal
                if comma_count == 1 and len(cleaned.split(',')[1]) <= 2:
                    # Decimal separator
                    cleaned = cleaned.replace(',', '.')
                else:
                    # Thousands separator
                    cleaned = cleaned.replace(',', '')

            elif dot_count > 0 and comma_count == 0:
                # Only dots - could be decimal separator or thousands separator
                # If there's only one dot and it's near the end (last 3 chars), it's decimal
                if dot_count == 1 and len(cleaned.split('.')[1]) <= 2:
                    # Already in correct format (decimal separator)
                    pass
                else:
                    # Thousands separator
                    cleaned = cleaned.replace('.', '')

            else:
                # Both dots and commas present
                # Find which one appears last
                last_dot = cleaned.rfind('.')
                last_comma = cleaned.rfind(',')

                if last_comma > last_dot:
                    # Comma is decimal separator, dots are thousands
                    cleaned = cleaned.replace('.', '').replace(',', '.')
                else:
                    # Dot is decimal separator, commas are thousands
                    cleaned = cleaned.replace(',', '')

            return Decimal(cleaned)

        except Exception as e:
            self.logger.error(f"Error parsing Colombian number '{value_str}': {e}")
            return Decimal('0')

    def _extract_product_table(self, page) -> List[Dict[str, Any]]:
        """
        Extract product table from PDF page

        Expected columns:
        Línea | Referencia | Descripción | Cant.Bultos | Cant.Kilos |
        Precio Unitario | Valor Total | Valor IVA | Iva%

        Args:
            page: pdfplumber page object

        Returns:
            List of item dictionaries
        """
        items = []

        try:
            # Extract tables from page
            tables = page.extract_tables()

            if not tables:
                self.logger.warning("No tables found in PDF page")
                return items

            self.logger.info(f"Found {len(tables)} tables in PDF")

            # Find the products table (should contain "Referencia", "Descripción", etc.)
            products_table = None
            for table in tables:
                if not table or len(table) < 2:
                    continue

                # Check if this is the products table by looking at headers
                header_row = table[0]
                header_text = ' '.join([str(cell) if cell else '' for cell in header_row])

                if any(keyword in header_text.lower() for keyword in
                       ['referencia', 'descripción', 'descripcion', 'cantidad', 'kilos']):
                    products_table = table
                    break

            if not products_table:
                self.logger.warning("Products table not found in PDF")
                return items

            # Parse table headers to find column indices
            headers = products_table[0]
            col_map = self._map_table_columns(headers)

            self.logger.info(f"Column mapping: {col_map}")

            # Parse data rows (skip header)
            for row_idx, row in enumerate(products_table[1:], 1):
                try:
                    # Skip empty rows
                    if not row or all(not cell or str(cell).strip() == '' for cell in row):
                        continue

                    # Extract values from row
                    product_code = str(row[col_map.get('referencia', 1)] or '').strip()
                    product_name = str(row[col_map.get('descripcion', 2)] or '').strip()
                    quantity_bultos_str = str(row[col_map.get('cant_bultos', 3)] or '0').strip()
                    quantity_kilos_str = str(row[col_map.get('cant_kilos', 4)] or '0').strip()
                    line_total_str = str(row[col_map.get('valor_total', 6)] or '0').strip()
                    tax_percent_str = str(row[col_map.get('iva_percent', 8)] or '0').strip()

                    # Skip rows without product code
                    if not product_code:
                        continue

                    # Parse numbers using Colombian format
                    quantity_original = self._parse_colombian_number(quantity_bultos_str)
                    quantity_adjusted = self._parse_colombian_number(quantity_kilos_str)
                    line_total = self._parse_colombian_number(line_total_str)
                    tax_percentage = self._parse_colombian_number(tax_percent_str)

                    # Calculate unit price: line_total / quantity_adjusted
                    if quantity_adjusted > 0:
                        unit_price = line_total / quantity_adjusted
                    else:
                        unit_price = Decimal('0')
                        self.logger.warning(
                            f"Row {row_idx}: quantity_adjusted is 0 for product {product_code}"
                        )

                    item = {
                        'product_code': product_code,
                        'product_name': product_name,
                        'quantity_original': quantity_original,  # Bultos
                        'quantity_adjusted': quantity_adjusted,   # Kilos
                        'unit_of_measure': 'KG',
                        'unit_price': unit_price,  # CALCULATED
                        'tax_percentage': tax_percentage,
                        'line_total': line_total,
                        'quantity': quantity_adjusted,  # For compatibility with XML parser
                        'taxable_amount': line_total,  # Assuming line_total is before tax
                        'tax_amount': line_total * (tax_percentage / Decimal('100'))
                    }

                    items.append(item)

                    self.logger.info(
                        f"Row {row_idx}: {product_code} - {product_name[:30]} - "
                        f"Qty: {quantity_adjusted} KG - Price: ${unit_price:.2f}"
                    )

                except Exception as e:
                    self.logger.error(f"Error parsing row {row_idx}: {e}")
                    continue

            self.logger.info(f"Extracted {len(items)} items from product table")

        except Exception as e:
            self.logger.error(f"Error extracting product table: {e}", exc_info=True)

        return items

    def _map_table_columns(self, headers: List) -> Dict[str, int]:
        """
        Map table column names to indices

        Args:
            headers: List of header cells

        Returns:
            Dictionary mapping column names to indices
        """
        col_map = {}

        try:
            for idx, header in enumerate(headers):
                if not header:
                    continue

                header_lower = str(header).lower().strip()

                # Map common column names
                if 'referencia' in header_lower or 'ref' in header_lower:
                    col_map['referencia'] = idx
                elif 'descripci' in header_lower or 'descrip' in header_lower:
                    col_map['descripcion'] = idx
                elif 'bultos' in header_lower:
                    col_map['cant_bultos'] = idx
                elif 'kilos' in header_lower or 'kg' in header_lower:
                    col_map['cant_kilos'] = idx
                elif 'precio' in header_lower and 'unitario' in header_lower:
                    col_map['precio_unitario'] = idx
                elif 'valor' in header_lower and 'total' in header_lower:
                    col_map['valor_total'] = idx
                elif 'valor' in header_lower and 'iva' in header_lower:
                    col_map['valor_iva'] = idx
                elif 'iva' in header_lower and '%' in header_lower:
                    col_map['iva_percent'] = idx
                elif 'l' in header_lower and 'nea' in header_lower:  # Línea
                    col_map['linea'] = idx

        except Exception as e:
            self.logger.error(f"Error mapping table columns: {e}")

        return col_map
