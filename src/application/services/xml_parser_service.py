"""XML Parser Service - Application Layer"""
import logging
from typing import Optional
from src.domain.entities.invoice import Invoice
from src.domain.repositories.xml_parser_repository import XMLParserRepository


class XMLParserService:
    """Service for XML parsing operations"""

    def __init__(self, xml_parser_repo: XMLParserRepository, logger: logging.Logger):
        self.xml_parser_repo = xml_parser_repo
        self.logger = logger

    def parse_invoice_xml(self, xml_content: bytes) -> Optional[Invoice]:
        """Parse XML content to Invoice entity"""
        try:
            self.logger.debug("Parsing XML content")
            invoice = self.xml_parser_repo.parse_invoice(xml_content)

            if invoice:
                self.logger.info(f"Successfully parsed invoice {invoice.invoice_number}")
            else:
                self.logger.warning("Failed to parse invoice")

            return invoice

        except Exception as e:
            self.logger.error(f"Error parsing XML: {str(e)}")
            return None

    def validate_xml_structure(self, xml_content: bytes) -> bool:
        """Validate XML structure"""
        try:
            return self.xml_parser_repo.validate_xml(xml_content)
        except Exception as e:
            self.logger.error(f"Error validating XML: {str(e)}")
            return False
