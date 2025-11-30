"""Email Service - Application Layer"""
import logging
from typing import List
from ...domain.entities.client import Client
from ...domain.repositories.email_repository import EmailRepository


class EmailService:
    """Service for email operations"""

    def __init__(self, email_repo: EmailRepository, logger: logging.Logger):
        self.email_repo = email_repo
        self.logger = logger

    def connect_to_email(self, email: str, password: str, client: Client) -> bool:
        """Connect to email server for a client"""
        try:
            self.logger.info(f"Connecting to email server for {client.name}")
            return self.email_repo.connect(email, password, client.imap_server)
        except Exception as e:
            self.logger.error(f"Failed to connect to email: {str(e)}")
            return False

    def get_unread_emails(self, client: Client) -> List[str]:
        """Get unread emails matching client criteria"""
        try:
            self.logger.info(f"Searching for emails for {client.name}")
            email_ids = self.email_repo.search_emails(client.search_criteria)
            self.logger.info(f"Found {len(email_ids)} emails")
            return email_ids
        except Exception as e:
            self.logger.error(f"Error searching emails: {str(e)}")
            return []

    def disconnect(self) -> None:
        """Disconnect from email server"""
        try:
            self.email_repo.disconnect()
        except Exception as e:
            self.logger.error(f"Error disconnecting: {str(e)}")
