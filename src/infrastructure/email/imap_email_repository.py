"""IMAP Email Repository Implementation - Infrastructure Layer"""
import imaplib
import email
from email.header import decode_header
from typing import List, Tuple, Optional
from src.domain.repositories.email_repository import EmailRepository


class IMAPEmailRepository(EmailRepository):
    """IMAP implementation of email repository"""

    def __init__(self):
        self.imap: Optional[imaplib.IMAP4_SSL] = None

    def connect(self, email_addr: str, password: str, imap_server: str) -> bool:
        """Connect to IMAP server"""
        try:
            self.imap = imaplib.IMAP4_SSL(imap_server)
            self.imap.login(email_addr, password)
            self.imap.select('INBOX')
            return True
        except Exception as e:
            raise ConnectionError(f"Failed to connect to IMAP server: {str(e)}")

    def search_emails(self, search_criteria: str) -> List[str]:
        """Search emails by criteria"""
        if not self.imap:
            raise ConnectionError("Not connected to IMAP server")

        try:
            # Parse search criteria
            status, messages = self.imap.search(None, search_criteria)

            if status != 'OK':
                return []

            email_ids = messages[0].split()
            return [msg_id.decode() for msg_id in email_ids]

        except Exception as e:
            raise RuntimeError(f"Error searching emails: {str(e)}")

    def fetch_email(self, email_id: str) -> Tuple[bytes, dict]:
        """Fetch email by ID"""
        if not self.imap:
            raise ConnectionError("Not connected to IMAP server")

        try:
            status, msg_data = self.imap.fetch(email_id, '(RFC822)')

            if status != 'OK':
                raise RuntimeError(f"Failed to fetch email {email_id}")

            email_body = msg_data[0][1]
            msg = email.message_from_bytes(email_body)

            # Extract basic info
            email_info = {
                'subject': self._decode_header(msg['Subject']),
                'from': self._decode_header(msg['From']),
                'date': msg['Date']
            }

            return email_body, email_info

        except Exception as e:
            raise RuntimeError(f"Error fetching email {email_id}: {str(e)}")

    def extract_attachments(self, email_data: bytes) -> List[Tuple[str, bytes]]:
        """Extract attachments from email"""
        attachments = []

        try:
            msg = email.message_from_bytes(email_data)

            for part in msg.walk():
                if part.get_content_maintype() == 'multipart':
                    continue

                if part.get('Content-Disposition') is None:
                    continue

                filename = part.get_filename()
                if filename:
                    filename = self._decode_header(filename)
                    content = part.get_payload(decode=True)
                    attachments.append((filename, content))

        except Exception as e:
            raise RuntimeError(f"Error extracting attachments: {str(e)}")

        return attachments

    def disconnect(self) -> None:
        """Disconnect from IMAP server"""
        if self.imap:
            try:
                self.imap.close()
                self.imap.logout()
            except:
                pass
            finally:
                self.imap = None

    def _decode_header(self, header_value: str) -> str:
        """Decode email header"""
        if not header_value:
            return ""

        decoded_parts = decode_header(header_value)
        decoded_string = ""

        for part, encoding in decoded_parts:
            if isinstance(part, bytes):
                try:
                    decoded_string += part.decode(encoding or 'utf-8')
                except:
                    decoded_string += part.decode('utf-8', errors='ignore')
            else:
                decoded_string += part

        return decoded_string
