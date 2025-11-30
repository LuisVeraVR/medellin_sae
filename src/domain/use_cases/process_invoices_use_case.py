"""Process Invoices Use Case - Domain Layer"""
import logging
import zipfile
import io
from typing import List
from datetime import datetime
from ..entities.client import Client
from ..entities.invoice import Invoice
from ..entities.processing_result import ProcessingResult
from ..repositories.email_repository import EmailRepository
from ..repositories.xml_parser_repository import XMLParserRepository
from ..repositories.database_repository import DatabaseRepository
from ..repositories.csv_repository import CSVRepository


class ProcessInvoicesUseCase:
    """Use case for processing invoices from emails"""

    def __init__(
        self,
        email_repo: EmailRepository,
        xml_parser_repo: XMLParserRepository,
        database_repo: DatabaseRepository,
        csv_repo: CSVRepository,
        logger: logging.Logger
    ):
        self.email_repo = email_repo
        self.xml_parser_repo = xml_parser_repo
        self.database_repo = database_repo
        self.csv_repo = csv_repo
        self.logger = logger

    def execute(
        self,
        client: Client,
        email: str,
        password: str,
        output_dir: str
    ) -> ProcessingResult:
        """Execute invoice processing for a client"""
        result = ProcessingResult(
            client_id=client.id,
            timestamp=datetime.now()
        )

        try:
            # Connect to email server
            if not self.email_repo.connect(email, password, client.imap_server):
                result.add_error("Failed to connect to email server")
                return result

            # Search for unread emails
            email_ids = self.email_repo.search_emails(client.search_criteria)
            self.logger.info(f"Found {len(email_ids)} emails for {client.name}")

            invoices = []

            for email_id in email_ids:
                # Check if already processed
                if self.database_repo.is_email_processed(email_id):
                    self.logger.info(f"Email {email_id} already processed, skipping")
                    continue

                try:
                    # Fetch email
                    email_data, email_info = self.email_repo.fetch_email(email_id)
                    result.increment_emails()

                    # Extract attachments
                    attachments = self.email_repo.extract_attachments(email_data)

                    # Process ZIP files
                    for filename, content in attachments:
                        if filename.lower().endswith('.zip'):
                            invoice = self._process_zip_attachment(content, client)
                            if invoice:
                                invoices.append(invoice)
                                result.increment_invoices()

                    # Mark email as processed
                    self.database_repo.mark_email_processed(email_id, datetime.now())

                except Exception as e:
                    error_msg = f"Error processing email {email_id}: {str(e)}"
                    self.logger.error(error_msg)
                    result.add_error(error_msg)

            # Export invoices to CSV
            if invoices:
                csv_file = self.csv_repo.export_invoices(invoices, client, output_dir)
                result.output_file = csv_file
                self.logger.info(f"Exported {len(invoices)} invoices to {csv_file}")

            # Disconnect
            self.email_repo.disconnect()

        except Exception as e:
            error_msg = f"Fatal error processing invoices: {str(e)}"
            self.logger.error(error_msg)
            result.add_error(error_msg)

        return result

    def _process_zip_attachment(self, zip_content: bytes, client: Client) -> Invoice:
        """Process ZIP attachment to extract invoice"""
        try:
            with zipfile.ZipFile(io.BytesIO(zip_content)) as zf:
                # Find XML file
                xml_files = [f for f in zf.namelist() if f.lower().endswith('.xml')]

                if not xml_files:
                    self.logger.warning("No XML file found in ZIP")
                    return None

                # Parse first XML file
                xml_content = zf.read(xml_files[0])
                invoice = self.xml_parser_repo.parse_invoice(xml_content)

                return invoice

        except Exception as e:
            self.logger.error(f"Error processing ZIP: {str(e)}")
            return None
