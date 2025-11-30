"""Database Repository Interface - Domain Layer"""
from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime


class DatabaseRepository(ABC):
    """Abstract interface for database operations"""

    @abstractmethod
    def is_email_processed(self, email_id: str) -> bool:
        """Check if email has been processed"""
        pass

    @abstractmethod
    def mark_email_processed(self, email_id: str, timestamp: datetime) -> None:
        """Mark email as processed"""
        pass

    @abstractmethod
    def save_invoice_record(self, invoice_number: str, email_id: str,
                           timestamp: datetime, csv_file: str) -> None:
        """Save invoice processing record"""
        pass

    @abstractmethod
    def log_processing(self, level: str, message: str, timestamp: datetime) -> None:
        """Log processing event to database"""
        pass

    @abstractmethod
    def get_processing_stats(self) -> dict:
        """Get processing statistics"""
        pass
