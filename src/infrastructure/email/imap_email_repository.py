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
            # Try to connect with SSL
            self.imap = imaplib.IMAP4_SSL(imap_server, 993)

            # Enable debug if needed (shows IMAP conversation)
            # self.imap.debug = 4

            # Try login
            result = self.imap.login(email_addr, password)

            # Select INBOX
            self.imap.select('INBOX')
            return True

        except imaplib.IMAP4.error as e:
            error_msg = str(e)

            # Provide helpful error messages
            if b'LOGIN failed' in str(e).encode() or 'LOGIN failed' in str(e):
                raise ConnectionError(
                    f"Failed to login to IMAP server: {error_msg}\n\n"
                    "Posibles soluciones:\n"
                    "1. Verifica que IMAP esté habilitado en tu cuenta de Outlook\n"
                    "   (Outlook Web > Configuración > Ver toda la configuración > Correo > Sincronizar correo)\n"
                    "2. Si tienes verificación en 2 pasos, usa una 'Contraseña de aplicación':\n"
                    "   - Cuenta Microsoft: https://account.microsoft.com/security\n"
                    "   - Office 365: https://mysignins.microsoft.com/security-info\n"
                    "3. Ejecuta 'python test_imap.py' para diagnosticar el problema\n"
                )
            else:
                raise ConnectionError(f"IMAP error: {error_msg}")

        except Exception as e:
            raise ConnectionError(
                f"Failed to connect to IMAP server: {str(e)}\n"
                f"Servidor: {imap_server}:993\n"
                f"Email: {email_addr}\n"
                "Ejecuta 'python test_imap.py' para diagnosticar"
            )

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
