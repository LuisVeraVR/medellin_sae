"""XML Parser Repository Interface - Domain Layer"""
from abc import ABC, abstractmethod
from typing import Optional
from src.domain.entities.invoice import Invoice


class XMLParserRepository(ABC):
    """Abstract interface for XML parsing operations"""

    @abstractmethod
    def parse_invoice(self, xml_content: bytes) -> Optional[Invoice]:
        """Parse XML content and return Invoice entity"""
        pass

    @abstractmethod
    def validate_xml(self, xml_content: bytes) -> bool:
        """Validate XML structure"""
        pass
