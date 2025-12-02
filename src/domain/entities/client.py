"""Client Entity - Domain Layer"""
from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class Client:
    """Represents a client configuration"""

    id: str
    name: str
    enabled: bool
    email_config: Dict[str, Any]
    xml_config: Dict[str, Any]
    output_config: Dict[str, Any]

    @property
    def search_criteria(self) -> str:
        """Get email search criteria"""
        return self.email_config.get('search_criteria', '')

    @property
    def imap_server(self) -> str:
        """Get IMAP server"""
        return self.email_config.get('imap_server', '')

    @property
    def csv_delimiter(self) -> str:
        """Get CSV delimiter"""
        return self.output_config.get('csv_delimiter', ';')

    @property
    def decimal_separator(self) -> str:
        """Get decimal separator"""
        return self.output_config.get('decimal_separator', ',')

    @property
    def decimal_places(self) -> int:
        """Get decimal places"""
        return self.output_config.get('decimal_places', 5)
