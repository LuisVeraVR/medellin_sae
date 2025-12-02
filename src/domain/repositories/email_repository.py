"""Email Repository Interface - Domain Layer"""
from abc import ABC, abstractmethod
from typing import List, Tuple
from src.domain.entities.client import Client


class EmailRepository(ABC):
    """Abstract interface for email operations"""

    @abstractmethod
    def connect(self, email: str, password: str, imap_server: str) -> bool:
        """Connect to email server"""
        pass

    @abstractmethod
    def search_emails(self, search_criteria: str) -> List[str]:
        """Search emails by criteria"""
        pass

    @abstractmethod
    def fetch_email(self, email_id: str) -> Tuple[bytes, dict]:
        """Fetch email by ID"""
        pass

    @abstractmethod
    def extract_attachments(self, email_data: bytes) -> List[Tuple[str, bytes]]:
        """Extract attachments from email"""
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Disconnect from email server"""
        pass
