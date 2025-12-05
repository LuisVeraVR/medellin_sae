"""UBL 2.1 XML Parser Implementation - Infrastructure Layer"""
from lxml import etree
from decimal import Decimal
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from src.domain.entities.invoice import Invoice
from src.domain.entities.invoice_item import InvoiceItem
from src.domain.repositories.xml_parser_repository import XMLParserRepository

if TYPE_CHECKING:
    from src.application.services.pulgarin_inventory_service import PulgarinInventoryService


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

    def __init__(self, inventory_service: Optional['PulgarinInventoryService'] = None):
        """
        Initialize UBL XML Parser

        Args:
            inventory_service: Optional Pulgarin inventory service for weight lookup
        """
        self.inventory_service = inventory_service

    # Mapeo de códigos de unidad UBL a nombres legibles
    # Basado en UN/ECE Recommendation 20
    UNIT_CODE_MAP = {
        '94': 'KG',   # Kilogramo
        'KGM': 'KG',  # Kilogramo
        'GRM': 'GR',  # Gramo
        'LTR': 'LT',  # Litro
        'MTR': 'MT',  # Metro
        'H87': 'UN',  # Unidad
        'EA': 'UN',   # Unidad (Each)
        'NIU': 'UN',  # Número de unidades
        'C62': 'UN',  # Unidad
    }

    def parse_invoice(self, xml_content: bytes) -> Optional[Invoice]:
        """Parse UBL 2.1 XML and return Invoice entity"""
        try:
            tree = etree.fromstring(xml_content)

            # Check if this is an AttachedDocument wrapper
            # If so, extract the Invoice from the CDATA inside cac:Attachment
            root_tag = tree.tag
            if 'AttachedDocument' in root_tag:
                # Extract Invoice from CDATA in cac:Attachment/cac:ExternalReference/cbc:Description
                cdata_element = tree.find('.//cac:Attachment/cac:ExternalReference/cbc:Description', self.NAMESPACES)
                if cdata_element is not None and cdata_element.text:
                    # Parse the CDATA content as a new XML
                    invoice_xml = cdata_element.text.strip()
                    # Remove CDATA markers if present
                    if invoice_xml.startswith('<![CDATA['):
                        invoice_xml = invoice_xml[9:-3]  # Remove <![CDATA[ and ]]>
                    # Parse the Invoice XML
                    tree = etree.fromstring(invoice_xml.encode('utf-8'))

            # Extract invoice header information
            invoice_number = self._get_text(tree, './/cbc:ID')
            invoice_date = self._get_date(tree, './/cbc:IssueDate')

            # Try PaymentDueDate first, then DueDate as fallback
            payment_date = self._get_date(tree, './/cbc:PaymentDueDate')
            if not payment_date:
                payment_date = self._get_date(tree, './/cbc:DueDate')

            # Get municipality from buyer's address
            municipality = self._get_text(tree, './/cac:AccountingCustomerParty/cac:Party/cac:PhysicalLocation/cac:Address/cbc:CityName')

            # Fallback: try DeliveryLocation if not found in buyer's address
            if not municipality:
                municipality = self._get_text(tree, './/cac:DeliveryLocation//cbc:CityName')

            # Extract invoice notes/description
            description = self._get_text(tree, './/cbc:Note')

            # Extract currency code and convert to numeric
            currency_code = self._get_text(tree, './/cbc:DocumentCurrencyCode')
            if currency_code == 'COP':
                currency = "1"
            elif currency_code == 'USD':
                currency = "2"
            elif currency_code == 'EUR':
                currency = "3"
            else:
                currency = "1"  # Default to COP

            # Extract seller information
            seller_party = tree.find('.//cac:AccountingSupplierParty/cac:Party', self.NAMESPACES)
            seller_nit = self._get_text(seller_party, './/cac:PartyTaxScheme/cbc:CompanyID') if seller_party is not None else ""
            seller_name = self._get_text(seller_party, './/cac:PartyName/cbc:Name') if seller_party is not None else ""

            if not seller_name:
                seller_name = self._get_text(seller_party, './/cac:PartyLegalEntity/cbc:RegistrationName') if seller_party is not None else ""

            # Extract buyer information
            buyer_party = tree.find('.//cac:AccountingCustomerParty/cac:Party', self.NAMESPACES)

            # Try multiple locations for buyer NIT
            buyer_nit = ""
            if buyer_party is not None:
                # Try Party/cbc:ID first (common in Colombian invoices)
                buyer_nit = self._get_text(buyer_party, './/cbc:ID')
                # If not found, try PartyTaxScheme/cbc:CompanyID
                if not buyer_nit:
                    buyer_nit = self._get_text(buyer_party, './/cac:PartyTaxScheme/cbc:CompanyID')

            # Try multiple locations for buyer name
            buyer_name = ""
            if buyer_party is not None:
                # Try RegistrationName first
                buyer_name = self._get_text(buyer_party, './/cac:PartyLegalEntity/cbc:RegistrationName')
                # If not found, try PartyName
                if not buyer_name:
                    buyer_name = self._get_text(buyer_party, './/cac:PartyName/cbc:Name')

            # Create invoice
            invoice = Invoice(
                invoice_number=invoice_number,
                invoice_date=invoice_date,
                payment_date=payment_date,
                seller_nit=seller_nit,
                seller_name=seller_name,
                buyer_nit=buyer_nit,
                buyer_name=buyer_name,
                municipality=municipality or "",
                description=description or None,
                currency=currency,
                active="1",  # Siempre 1
                invoice_active="1",  # Siempre 1
                principal_vc="V"  # V = Vendedor (dueño de la factura)
            )

            # Extract line items (after CDATA extraction, InvoiceLines are directly in Invoice)
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

            # Get unit code and convert to readable name
            unit_code_element = line_element.find('.//cbc:InvoicedQuantity', self.NAMESPACES)
            unit_code = unit_code_element.get('unitCode', '') if unit_code_element is not None else ''

            # Map unit code to readable name (e.g., 94 -> KG)
            unit_of_measure = self.UNIT_CODE_MAP.get(unit_code, unit_code)

            # Price
            price_str = self._get_text(line_element, './/cac:Price/cbc:PriceAmount')
            unit_price = Decimal(price_str) if price_str else Decimal('0')

            # Tax percentage - in Pulgarin invoices it's inside TaxCategory
            tax_percent_str = self._get_text(line_element, './/cac:TaxTotal/cac:TaxSubtotal/cac:TaxCategory/cbc:Percent')

            # Fallback: try without TaxCategory for other formats
            if not tax_percent_str:
                tax_percent_str = self._get_text(line_element, './/cac:TaxTotal/cac:TaxSubtotal/cbc:Percent')

            tax_percentage = Decimal(tax_percent_str) if tax_percent_str else Decimal('0')

            # Extract weight (PESO)
            weight = None

            # First priority: Look up in inventory by product name
            if self.inventory_service and product_name:
                weight = self.inventory_service.get_weight(product_name)
                if weight:
                    # Also get unit of measure from inventory if available
                    inventory_unit = self.inventory_service.get_unit_of_measure(product_name)
                    if inventory_unit:
                        unit_of_measure = inventory_unit

            # Second priority: Extract from XML (if not found in inventory)
            if weight is None:
                # Try cbc:Weight
                weight_str = self._get_text(line_element, './/cac:Item/cbc:Weight')
                if not weight_str:
                    # Try cbc:NetWeight
                    weight_str = self._get_text(line_element, './/cac:Item/cbc:NetWeight')
                if not weight_str:
                    # Try ItemProperty with Name containing "peso" or "weight"
                    properties = line_element.findall('.//cac:Item/cac:ItemProperty', self.NAMESPACES)
                    for prop in properties:
                        name = self._get_text(prop, './/cbc:Name')
                        if name and ('peso' in name.lower() or 'weight' in name.lower()):
                            weight_str = self._get_text(prop, './/cbc:Value')
                            if weight_str:
                                break

                if weight_str:
                    try:
                        weight = Decimal(weight_str)
                    except:
                        weight = None

            return InvoiceItem(
                product_name=product_name or "",
                product_code=product_code or "",
                subyacente_code="SPN-1",  # Código subyacente hardcoded
                quantity=quantity,
                unit_of_measure=unit_of_measure,
                unit_price=unit_price,
                tax_percentage=tax_percentage,
                weight=weight
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
