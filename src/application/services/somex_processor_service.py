"""Somex Processor Service - Application Layer"""
import logging
import zipfile
import io
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from lxml import etree
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
from decimal import Decimal
from datetime import datetime

from src.infrastructure.database.somex_repository import SomexRepository
from src.infrastructure.sftp.somex_sftp_client import SomexSftpClient


class ItemsImporter:
    """Helper class to import items from Excel file"""

    def __init__(self, logger: logging.Logger):
        self.logger = logger

    def import_items_from_excel(self, excel_path: str) -> List[Dict[str, Any]]:
        """
        Import items from Excel file

        Expected columns:
        CodigoItem, Referencia, Descripcion, IdPlan, DescPlan,
        IdMayor, DescripcionPlan, RowIdItem, Categoria

        Args:
            excel_path: Path to Excel file

        Returns:
            List of item dictionaries
        """
        items = []

        try:
            wb = openpyxl.load_workbook(excel_path, read_only=True)
            ws = wb.active

            # Read headers from first row
            headers = []
            for cell in ws[1]:
                headers.append(cell.value)

            self.logger.info(f"Excel headers: {headers}")

            # Map expected columns (case insensitive)
            column_map = {}
            expected_columns = [
                'CodigoItem', 'Referencia', 'Descripcion', 'IdPlan', 'DescPlan',
                'IdMayor', 'DescripcionPlan', 'RowIdItem', 'Categoria'
            ]

            for expected in expected_columns:
                for idx, header in enumerate(headers):
                    if header and expected.lower() == str(header).lower().replace(' ', ''):
                        column_map[expected] = idx
                        break

            self.logger.info(f"Column mapping: {column_map}")

            # Read data rows
            for row in ws.iter_rows(min_row=2, values_only=True):
                item = {
                    'codigo_item': str(row[column_map.get('CodigoItem', 0)] or '').strip(),
                    'referencia': str(row[column_map.get('Referencia', 1)] or '').strip(),
                    'descripcion': str(row[column_map.get('Descripcion', 2)] or '').strip(),
                    'id_plan': str(row[column_map.get('IdPlan', 3)] or '').strip(),
                    'desc_plan': str(row[column_map.get('DescPlan', 4)] or '').strip(),
                    'id_mayor': str(row[column_map.get('IdMayor', 5)] or '').strip(),
                    'descripcion_plan': str(row[column_map.get('DescripcionPlan', 6)] or '').strip(),
                    'row_id_item': str(row[column_map.get('RowIdItem', 7)] or '').strip(),
                    'categoria': str(row[column_map.get('Categoria', 8)] or '').strip(),
                }

                # Only add if has codigo_item
                if item['codigo_item']:
                    items.append(item)

            wb.close()

            self.logger.info(f"Imported {len(items)} items from Excel")

        except Exception as e:
            self.logger.error(f"Error importing items from Excel: {e}")
            raise

        return items


class SomexProcessorService:
    """Service for processing Somex ZIP files and generating Excel reports"""

    # UBL Namespaces
    NAMESPACES = {
        'cac': 'urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2',
        'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2',
        'ext': 'urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2',
    }

    def __init__(
        self,
        repository: SomexRepository,
        logger: logging.Logger,
        output_dir: str = "output/somex"
    ):
        self.repository = repository
        self.logger = logger
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def extract_xmls_from_zip(self, zip_path: str) -> List[Tuple[str, bytes]]:
        """
        Extract XML files from a ZIP archive

        Args:
            zip_path: Path to ZIP file

        Returns:
            List of tuples (filename, xml_content)
        """
        xml_files = []

        try:
            self.logger.info(f"Opening ZIP file: {zip_path}")

            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                all_files = zip_ref.namelist()
                self.logger.info(f"Files in ZIP: {all_files}")

                for file_info in zip_ref.filelist:
                    self.logger.debug(f"Checking file: {file_info.filename}")

                    if file_info.filename.lower().endswith('.xml'):
                        self.logger.info(f"Reading XML: {file_info.filename}")
                        xml_content = zip_ref.read(file_info.filename)
                        self.logger.info(
                            f"XML content size: {len(xml_content)} bytes"
                        )
                        xml_files.append((file_info.filename, xml_content))

            self.logger.info(
                f"Extracted {len(xml_files)} XML files from {Path(zip_path).name}"
            )

        except zipfile.BadZipFile as e:
            self.logger.error(f"Invalid ZIP file {zip_path}: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Error extracting XMLs from ZIP {zip_path}: {e}")
            raise

        return xml_files

    def extract_xmls_from_zip_bytes(
        self,
        zip_content: bytes,
        zip_filename: str
    ) -> List[Tuple[str, bytes]]:
        """
        Extract XML files from ZIP bytes

        Args:
            zip_content: ZIP file content as bytes
            zip_filename: Name of the ZIP file

        Returns:
            List of tuples (filename, xml_content)
        """
        xml_files = []

        try:
            with zipfile.ZipFile(io.BytesIO(zip_content), 'r') as zip_ref:
                for file_info in zip_ref.filelist:
                    if file_info.filename.lower().endswith('.xml'):
                        xml_content = zip_ref.read(file_info.filename)
                        xml_files.append((file_info.filename, xml_content))

            self.logger.info(
                f"Extracted {len(xml_files)} XML files from {zip_filename}"
            )

        except Exception as e:
            self.logger.error(
                f"Error extracting XMLs from ZIP {zip_filename}: {e}"
            )
            raise

        return xml_files

    def parse_invoice_xml(self, xml_content: bytes) -> Optional[Dict[str, Any]]:
        """
        Parse invoice XML and extract required data

        Args:
            xml_content: XML content as bytes

        Returns:
            Dictionary with invoice data
        """
        try:
            self.logger.info(f"Parsing XML content ({len(xml_content)} bytes)")
            tree = etree.fromstring(xml_content)

            # Log root tag
            self.logger.info(f"XML root tag: {tree.tag}")

            # Extract invoice data
            invoice_data = {
                'invoice_number': self._get_text(tree, './/cbc:ID'),
                'invoice_date': self._get_text(tree, './/cbc:IssueDate'),
                'payment_date': self._get_text(tree, './/cbc:DueDate'),
                'municipality': self._get_text(
                    tree, './/cac:DeliveryLocation//cbc:CityName'
                ),
            }

            self.logger.info(f"Invoice number: {invoice_data['invoice_number']}")

            # Extract seller information
            seller_party = tree.find(
                './/cac:AccountingSupplierParty/cac:Party',
                self.NAMESPACES
            )
            if seller_party is not None:
                invoice_data['seller_nit'] = self._get_text(
                    seller_party, './/cac:PartyTaxScheme/cbc:CompanyID'
                )
                invoice_data['seller_name'] = (
                    self._get_text(seller_party, './/cac:PartyName/cbc:Name') or
                    self._get_text(
                        seller_party,
                        './/cac:PartyLegalEntity/cbc:RegistrationName'
                    )
                )

            # Extract buyer information
            buyer_party = tree.find(
                './/cac:AccountingCustomerParty/cac:Party',
                self.NAMESPACES
            )
            if buyer_party is not None:
                invoice_data['buyer_nit'] = self._get_text(
                    buyer_party, './/cac:PartyTaxScheme/cbc:CompanyID'
                )
                invoice_data['buyer_name'] = (
                    self._get_text(buyer_party, './/cac:PartyName/cbc:Name') or
                    self._get_text(
                        buyer_party,
                        './/cac:PartyLegalEntity/cbc:RegistrationName'
                    )
                )

            # Extract line items
            lines = tree.findall('.//cac:InvoiceLine', self.NAMESPACES)
            self.logger.info(f"Found {len(lines)} invoice lines")

            invoice_data['items'] = []

            for idx, line in enumerate(lines, 1):
                self.logger.debug(f"Parsing line item {idx}")
                item = self._parse_line_item(line)
                if item:
                    invoice_data['items'].append(item)
                    self.logger.debug(
                        f"  - Product: {item['product_name']}, "
                        f"Code: {item['product_code']}, "
                        f"Qty: {item['quantity']}"
                    )

            self.logger.info(
                f"Parsed invoice {invoice_data['invoice_number']} "
                f"with {len(invoice_data['items'])} items"
            )

            return invoice_data

        except Exception as e:
            self.logger.error(f"Error parsing XML: {e}", exc_info=True)
            return None

    def _parse_line_item(self, line_element) -> Optional[Dict[str, Any]]:
        """Parse a single invoice line item"""
        try:
            # Product information
            product_name = (
                self._get_text(line_element, './/cac:Item/cbc:Description') or
                self._get_text(line_element, './/cac:Item/cbc:Name')
            )

            product_code = self._get_text(
                line_element,
                './/cac:Item/cac:SellersItemIdentification/cbc:ID'
            )

            # Quantity
            quantity_str = self._get_text(line_element, './/cbc:InvoicedQuantity')
            quantity = Decimal(quantity_str) if quantity_str else Decimal('0')

            # Unit of measure
            unit_elem = line_element.find(
                './/cbc:InvoicedQuantity',
                self.NAMESPACES
            )
            unit_of_measure = (
                unit_elem.get('unitCode', '') if unit_elem is not None else ''
            )

            # Price
            price_str = self._get_text(
                line_element, './/cac:Price/cbc:PriceAmount'
            )
            unit_price = Decimal(price_str) if price_str else Decimal('0')

            # Tax percentage
            tax_percent_str = self._get_text(
                line_element,
                './/cac:TaxTotal/cac:TaxSubtotal/cbc:Percent'
            )
            tax_percentage = (
                Decimal(tax_percent_str) if tax_percent_str else Decimal('0')
            )

            return {
                'product_name': product_name or "",
                'product_code': product_code or "",
                'quantity': quantity,
                'unit_of_measure': unit_of_measure,
                'unit_price': unit_price,
                'tax_percentage': tax_percentage,
            }

        except Exception as e:
            self.logger.error(f"Error parsing line item: {e}")
            return None

    def _get_text(self, element, xpath: str) -> str:
        """Get text from XPath"""
        if element is None:
            return ""

        result = element.find(xpath, self.NAMESPACES)
        if result is not None and result.text:
            return result.text.strip()
        return ""

    def format_decimal(self, value: Decimal, decimals: int = 5) -> str:
        """Format decimal with specified decimals and comma separator"""
        # Format with 5 decimals
        formatted = f"{value:.{decimals}f}"
        # Replace dot with comma for decimal separator
        return formatted.replace('.', ',')

    def create_excel_template(
        self,
        invoice_data: Dict[str, Any],
        output_filename: Optional[str] = None
    ) -> str:
        """
        Create Excel file from invoice data using the specified template

        Args:
            invoice_data: Dictionary with invoice data
            output_filename: Optional output filename

        Returns:
            Path to created Excel file
        """
        if not output_filename:
            invoice_number = invoice_data.get('invoice_number', 'unknown')
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_filename = f"somex_invoice_{invoice_number}_{timestamp}.xlsx"

        output_path = self.output_dir / output_filename

        # Create workbook
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Facturas Somex"

        # Define headers according to specification
        headers = [
            "N° Factura",
            "Nombre Producto",
            "Codigo Subyacente",
            "Unidad Medida en Kg,Un,Lt",
            "Cantidad (5 decimales - separdor coma)",
            "Precio Unitario (5 decimales - separdor coma)",
            "Fecha Factura Año-Mes-Dia",
            "Fecha Pago Año-Mes-Dia",
            "Nit Comprador (Existente)",
            "Nombre Comprador",
            "Nit Vendedor (Existente)",
            "Nombre Vendedor",
            "Principal V,C",
            "Municipio (Nombre Exacto de la Ciudad)",
            "Iva (N°%)",
            "Descripción",
            "Activa",
            "Factura Activa",
            "Bodega",
            "Incentivo",
            "Cantidad Original (5 decimales - separdor coma)",
            "Moneda (1,2,3)"
        ]

        # Write headers with formatting
        header_fill = PatternFill(
            start_color="366092",
            end_color="366092",
            fill_type="solid"
        )
        header_font = Font(bold=True, color="FFFFFF")

        for col_num, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col_num)
            cell.value = header
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal='center', vertical='center')

        # Write data rows
        row_num = 2
        for item in invoice_data.get('items', []):
            ws.cell(row=row_num, column=1).value = invoice_data.get(
                'invoice_number', ''
            )
            ws.cell(row=row_num, column=2).value = item.get('product_name', '')
            ws.cell(row=row_num, column=3).value = item.get('product_code', '')
            ws.cell(row=row_num, column=4).value = item.get('unit_of_measure', '')

            # Quantity with 5 decimals and comma separator
            ws.cell(row=row_num, column=5).value = self.format_decimal(
                item.get('quantity', Decimal('0'))
            )

            # Unit price with 5 decimals and comma separator
            ws.cell(row=row_num, column=6).value = self.format_decimal(
                item.get('unit_price', Decimal('0'))
            )

            ws.cell(row=row_num, column=7).value = invoice_data.get(
                'invoice_date', ''
            )
            ws.cell(row=row_num, column=8).value = invoice_data.get(
                'payment_date', ''
            )
            ws.cell(row=row_num, column=9).value = invoice_data.get(
                'buyer_nit', ''
            )
            ws.cell(row=row_num, column=10).value = invoice_data.get(
                'buyer_name', ''
            )
            ws.cell(row=row_num, column=11).value = invoice_data.get(
                'seller_nit', ''
            )
            ws.cell(row=row_num, column=12).value = invoice_data.get(
                'seller_name', ''
            )
            ws.cell(row=row_num, column=13).value = ""  # Principal V,C
            ws.cell(row=row_num, column=14).value = invoice_data.get(
                'municipality', ''
            )
            ws.cell(row=row_num, column=15).value = str(
                item.get('tax_percentage', '')
            )
            ws.cell(row=row_num, column=16).value = ""  # Descripción
            ws.cell(row=row_num, column=17).value = ""  # Activa
            ws.cell(row=row_num, column=18).value = ""  # Factura Activa
            ws.cell(row=row_num, column=19).value = ""  # Bodega
            ws.cell(row=row_num, column=20).value = ""  # Incentivo

            # Cantidad Original with 5 decimals and comma separator
            ws.cell(row=row_num, column=21).value = self.format_decimal(
                item.get('quantity', Decimal('0'))
            )

            ws.cell(row=row_num, column=22).value = ""  # Moneda

            row_num += 1

        # Auto-adjust column widths
        for column in ws.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            ws.column_dimensions[column_letter].width = adjusted_width

        # Save workbook
        wb.save(output_path)
        self.logger.info(f"Excel file created: {output_path}")

        return str(output_path)

    def process_zip_file(
        self,
        zip_path: str,
        zip_filename: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a ZIP file: extract XMLs and parse them

        Args:
            zip_path: Path to ZIP file
            zip_filename: Optional ZIP filename for logging

        Returns:
            Dictionary with processing results including parsed invoices
        """
        if not zip_filename:
            zip_filename = Path(zip_path).name

        results = {
            'zip_filename': zip_filename,
            'total_xmls': 0,
            'processed_xmls': 0,
            'skipped_xmls': 0,
            'failed_xmls': 0,
            'invoices': []  # List of parsed invoice data
        }

        try:
            # Extract XMLs from ZIP
            xml_files = self.extract_xmls_from_zip(zip_path)
            results['total_xmls'] = len(xml_files)

            for xml_filename, xml_content in xml_files:
                # Check if already processed
                if self.repository.is_xml_processed(xml_content):
                    self.logger.info(f"Skipping already processed XML: {xml_filename}")
                    results['skipped_xmls'] += 1
                    continue

                # Parse XML
                invoice_data = self.parse_invoice_xml(xml_content)

                if not invoice_data:
                    self.logger.warning(f"Failed to parse XML: {xml_filename}")
                    results['failed_xmls'] += 1
                    continue

                # Add metadata to invoice data
                invoice_data['xml_filename'] = xml_filename
                invoice_data['xml_content'] = xml_content
                invoice_data['zip_filename'] = zip_filename

                results['invoices'].append(invoice_data)
                results['processed_xmls'] += 1

                self.logger.info(f"Parsed XML {xml_filename}")

        except Exception as e:
            self.logger.error(f"Error processing ZIP file {zip_filename}: {e}")
            raise

        return results

    def create_consolidated_excel(
        self,
        all_invoices: List[Dict[str, Any]],
        output_filename: Optional[str] = None
    ) -> str:
        """
        Create a single Excel file with all invoices from multiple ZIPs

        Args:
            all_invoices: List of invoice data dictionaries
            output_filename: Optional output filename

        Returns:
            Path to created Excel file
        """
        if not output_filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_filename = f"somex_facturas_consolidadas_{timestamp}.xlsx"

        output_path = self.output_dir / output_filename

        # Create workbook
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Facturas Somex"

        # Define headers according to specification
        headers = [
            "N° Factura",
            "Nombre Producto",
            "Codigo Subyacente",
            "Unidad Medida en Kg,Un,Lt",
            "Cantidad (5 decimales - separdor coma)",
            "Precio Unitario (5 decimales - separdor coma)",
            "Fecha Factura Año-Mes-Dia",
            "Fecha Pago Año-Mes-Dia",
            "Nit Comprador (Existente)",
            "Nombre Comprador",
            "Nit Vendedor (Existente)",
            "Nombre Vendedor",
            "Principal V,C",
            "Municipio (Nombre Exacto de la Ciudad)",
            "Iva (N°%)",
            "Descripción",
            "Activa",
            "Factura Activa",
            "Bodega",
            "Incentivo",
            "Cantidad Original (5 decimales - separdor coma)",
            "Moneda (1,2,3)"
        ]

        # Write headers with formatting
        header_fill = PatternFill(
            start_color="366092",
            end_color="366092",
            fill_type="solid"
        )
        header_font = Font(bold=True, color="FFFFFF")

        for col_num, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col_num)
            cell.value = header
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal='center', vertical='center')

        # Write data rows for all invoices
        row_num = 2
        for invoice_data in all_invoices:
            for item in invoice_data.get('items', []):
                ws.cell(row=row_num, column=1).value = invoice_data.get(
                    'invoice_number', ''
                )
                ws.cell(row=row_num, column=2).value = item.get('product_name', '')
                ws.cell(row=row_num, column=3).value = item.get('product_code', '')
                ws.cell(row=row_num, column=4).value = item.get('unit_of_measure', '')

                # Quantity with 5 decimals and comma separator
                ws.cell(row=row_num, column=5).value = self.format_decimal(
                    item.get('quantity', Decimal('0'))
                )

                # Unit price with 5 decimals and comma separator
                ws.cell(row=row_num, column=6).value = self.format_decimal(
                    item.get('unit_price', Decimal('0'))
                )

                ws.cell(row=row_num, column=7).value = invoice_data.get(
                    'invoice_date', ''
                )
                ws.cell(row=row_num, column=8).value = invoice_data.get(
                    'payment_date', ''
                )
                ws.cell(row=row_num, column=9).value = invoice_data.get(
                    'buyer_nit', ''
                )
                ws.cell(row=row_num, column=10).value = invoice_data.get(
                    'buyer_name', ''
                )
                ws.cell(row=row_num, column=11).value = invoice_data.get(
                    'seller_nit', ''
                )
                ws.cell(row=row_num, column=12).value = invoice_data.get(
                    'seller_name', ''
                )
                ws.cell(row=row_num, column=13).value = ""  # Principal V,C
                ws.cell(row=row_num, column=14).value = invoice_data.get(
                    'municipality', ''
                )
                ws.cell(row=row_num, column=15).value = str(
                    item.get('tax_percentage', '')
                )
                ws.cell(row=row_num, column=16).value = ""  # Descripción
                ws.cell(row=row_num, column=17).value = ""  # Activa
                ws.cell(row=row_num, column=18).value = ""  # Factura Activa
                ws.cell(row=row_num, column=19).value = ""  # Bodega
                ws.cell(row=row_num, column=20).value = ""  # Incentivo

                # Cantidad Original with 5 decimals and comma separator
                ws.cell(row=row_num, column=21).value = self.format_decimal(
                    item.get('quantity', Decimal('0'))
                )

                ws.cell(row=row_num, column=22).value = ""  # Moneda

                row_num += 1

        # Auto-adjust column widths
        for column in ws.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            ws.column_dimensions[column_letter].width = adjusted_width

        # Save workbook
        wb.save(output_path)
        self.logger.info(
            f"Consolidated Excel created: {output_path} with {row_num - 2} rows"
        )

        return str(output_path)
