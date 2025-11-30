"""UBL 2.1 XML Parser Implementation - Infrastructure Layer"""
from lxml import etree
from decimal import Decimal
from datetime import datetime
from typing import Optional
from ...domain.entities.invoice import Invoice
from ...domain.entities.invoice_item import InvoiceItem
from ...domain.repositories.xml_parser_repository import XMLParserRepository


class UBLXMLParser(XMLParserRepository):
    """UBL 2.1 XML parser for Colombian electronic invoices"""

    # UBL 2.1 Namespaces for Colombia
    NAMESPACES = {
        'cac': 'urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2',
        'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2',
        'ext': 'urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2',
        'sts': 'dian:gov:co:facturaelectronica:Structures-2-1',
        'inv': 'urn:oasis:names:specification:ubl:schema:xsd:Invoice-2'
    }

    def parse_invoice(self, xml_content: bytes) -> Optional[Invoice]:
        """Parse UBL 2.1 XML and return Invoice entity"""
        try:
            tree = etree.fromstring(xml_content)

            # Extract invoice header information
            invoice_number = self._get_text(tree, './/cbc:ID')
            invoice_date = self._get_date(tree, './/cbc:IssueDate')
            payment_date = self._get_date(tree, './/cbc:DueDate')
            municipality = self._get_text(tree, './/cac:DeliveryLocation//cbc:CityName')

            # Extract seller information
            seller_party = tree.find('.//cac:AccountingSupplierParty/cac:Party', self.NAMESPACES)
            seller_nit = self._get_text(seller_party, './/cac:PartyTaxScheme/cbc:CompanyID') if seller_party is not None else ""
            seller_name = self._get_text(seller_party, './/cac:PartyName/cbc:Name') if seller_party is not None else ""

            if not seller_name:
                seller_name = self._get_text(seller_party, './/cac:PartyLegalEntity/cbc:RegistrationName') if seller_party is not None else ""

            # Extract buyer information
            buyer_party = tree.find('.//cac:AccountingCustomerParty/cac:Party', self.NAMESPACES)
            buyer_nit = self._get_text(buyer_party, './/cac:PartyTaxScheme/cbc:CompanyID') if buyer_party is not None else ""
            buyer_name = self._get_text(buyer_party, './/cac:PartyName/cbc:Name') if buyer_party is not None else ""

            if not buyer_name:
                buyer_name = self._get_text(buyer_party, './/cac:PartyLegalEntity/cbc:RegistrationName') if buyer_party is not None else ""

            # Create invoice
            invoice = Invoice(
                invoice_number=invoice_number,
                invoice_date=invoice_date,
                payment_date=payment_date,
                seller_nit=seller_nit,
                seller_name=seller_name,
                buyer_nit=buyer_nit,
                buyer_name=buyer_name,
                municipality=municipality or ""
            )

            # Extract line items
            lines = tree.findall('.//cac:InvoiceLine', self.NAMESPACES)

            for line in lines:
                item = self._parse_line_item(line)
                if item:
                    invoice.add_item(item)

            return invoice

        except Exception as e:
            raise RuntimeError(f"Error parsing XML: {str(e)}")

    def _parse_line_item(self, line_element) -> Optional[InvoiceItem]:
        """Parse a single invoice line item"""
        try:
            # Product information
            product_name = self._get_text(line_element, './/cac:Item/cbc:Description')

            if not product_name:
                product_name = self._get_text(line_element, './/cac:Item/cbc:Name')

            product_code = self._get_text(line_element, './/cac:Item/cac:SellersItemIdentification/cbc:ID')

            # Quantity and unit
            quantity_str = self._get_text(line_element, './/cbc:InvoicedQuantity')
            quantity = Decimal(quantity_str) if quantity_str else Decimal('0')

            unit_code = line_element.find('.//cbc:InvoicedQuantity', self.NAMESPACES)
            unit_of_measure = unit_code.get('unitCode', '') if unit_code is not None else ''

            # Price
            price_str = self._get_text(line_element, './/cac:Price/cbc:PriceAmount')
            unit_price = Decimal(price_str) if price_str else Decimal('0')

            # Tax percentage
            tax_percent_str = self._get_text(line_element, './/cac:TaxTotal/cac:TaxSubtotal/cbc:Percent')
            tax_percentage = Decimal(tax_percent_str) if tax_percent_str else Decimal('0')

            return InvoiceItem(
                product_name=product_name or "",
                product_code=product_code or "",
                quantity=quantity,
                unit_of_measure=unit_of_measure,
                unit_price=unit_price,
                tax_percentage=tax_percentage
            )

        except Exception as e:
            raise RuntimeError(f"Error parsing line item: {str(e)}")

    def validate_xml(self, xml_content: bytes) -> bool:
        """Validate XML structure"""
        try:
            etree.fromstring(xml_content)
            return True
        except:
            return False

    def _get_text(self, element, xpath: str) -> str:
        """Get text from XPath"""
        if element is None:
            return ""

        result = element.find(xpath, self.NAMESPACES)
        if result is not None and result.text:
            return result.text.strip()
        return ""

    def _get_date(self, element, xpath: str) -> Optional[datetime]:
        """Get date from XPath"""
        date_str = self._get_text(element, xpath)
        if date_str:
            try:
                return datetime.strptime(date_str, '%Y-%m-%d').date()
            except:
                return None
        return None
