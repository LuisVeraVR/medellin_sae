"""Processing Result Entity - Domain Layer"""
from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime


@dataclass
class ProcessingResult:
    """Represents the result of invoice processing operation"""

    client_id: str
    timestamp: datetime
    emails_processed: int = 0
    invoices_generated: int = 0
    errors_count: int = 0
    success: bool = True
    error_messages: List[str] = field(default_factory=list)
    output_file: Optional[str] = None

    def add_error(self, error_message: str) -> None:
        """Add an error message"""
        self.error_messages.append(error_message)
        self.errors_count += 1
        self.success = False

    def increment_emails(self) -> None:
        """Increment emails processed counter"""
        self.emails_processed += 1

    def increment_invoices(self) -> None:
        """Increment invoices generated counter"""
        self.invoices_generated += 1
