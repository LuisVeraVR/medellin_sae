"""OAuth 2.0 IMAP Email Repository Implementation - Infrastructure Layer

This module implements OAuth 2.0 authentication for Office 365 IMAP using the Device Code Flow.
The Device Code Flow is ideal for applications that don't have a web browser or can't easily
display a web UI for authentication.

OAuth 2.0 Device Code Flow:
1. App requests device code from Azure AD
2. User visits verification URL and enters the code
3. App polls Azure AD for access token
4. Once user authenticates, app receives access token
5. App uses token to authenticate with IMAP via XOAUTH2
"""
import os
import imaplib
import email
import json
import logging
from email.header import decode_header
from typing import List, Tuple, Optional
from pathlib import Path
import sys

try:
    import msal
except ImportError:
    raise ImportError(
        "The 'msal' library is required for OAuth 2.0 authentication. "
        "Please install it with: pip install msal>=1.24.0"
    )

from src.domain.repositories.email_repository import EmailRepository


class OAuth2IMAPRepository(EmailRepository):
    """OAuth 2.0 implementation of IMAP email repository for Office 365

    This implementation uses Microsoft Authentication Library (MSAL) to obtain
    OAuth 2.0 access tokens for IMAP authentication. Tokens are cached locally
    to avoid repeated authentication prompts.

    Configuration sources (in order of priority):
        1. Environment variables (.env file) - for development
        2. OAuth config file (config/oauth_config.json) - for production builds
        - AZURE_CLIENT_ID: Your Azure AD application (client) ID
        - AZURE_TENANT_ID: Your Azure AD tenant ID or "common" for multi-tenant
    """

    # Required scope for IMAP access in Office 365
    SCOPES = ["https://outlook.office365.com/IMAP.AccessAsUser.All"]

    # Token cache file location
    TOKEN_CACHE_FILE = "data/oauth_token_cache.json"

    # OAuth config file location
    OAUTH_CONFIG_FILE = "config/oauth_config.json"

    def __init__(self):
        """Initialize OAuth 2.0 IMAP repository"""
        self.imap: Optional[imaplib.IMAP4_SSL] = None
        self.logger = logging.getLogger(__name__)

        # Load Azure AD credentials
        self.client_id, tenant_id = self._load_azure_credentials()

        if not self.client_id:
            raise ValueError(
                "Azure AD no está configurado.\n\n"
                "OPCIÓN 1 - Para desarrollo local:\n"
                "  1. Crea un archivo .env en la raíz del proyecto\n"
                "  2. Agrega: AZURE_CLIENT_ID=tu-client-id-aqui\n\n"
                "OPCIÓN 2 - Para distribución (ejecutable):\n"
                "  1. Copia config/oauth_config.example.json a config/oauth_config.json\n"
                "  2. Edita oauth_config.json con tus credenciales de Azure AD\n"
                "  3. Ejecuta python build.py para incluirlo en el ejecutable\n\n"
                "Para obtener el Client ID:\n"
                "  1. Ve a Azure Portal (https://portal.azure.com)\n"
                "  2. Azure Active Directory → App registrations → New registration\n"
                "  3. Copia el Application (client) ID"
            )

        # Build authority URL
        self.authority = f"https://login.microsoftonline.com/{tenant_id}"

        self.logger.info(f"Initializing OAuth 2.0 with CLIENT_ID: {self.client_id[:8]}...")
        self.logger.info(f"Authority: {self.authority}")

        # Ensure token cache directory exists
        cache_path = Path(self.TOKEN_CACHE_FILE)
        cache_path.parent.mkdir(parents=True, exist_ok=True)

        # Initialize MSAL application with token cache
        self.token_cache = self._load_token_cache()
        self.app = msal.PublicClientApplication(
            client_id=self.client_id,
            authority=self.authority,
            token_cache=self.token_cache
        )

    def _load_azure_credentials(self) -> Tuple[Optional[str], str]:
        """Load Azure AD credentials from config file or environment

        Priority order:
        1. Environment variables (.env) - for development
        2. OAuth config file (config/oauth_config.json) - for production

        Returns:
            Tuple of (client_id, tenant_id)
        """
        client_id = None
        tenant_id = 'common'

        # Priority 1: Environment variables (.env file)
        env_client_id = os.getenv('AZURE_CLIENT_ID')
        env_tenant_id = os.getenv('AZURE_TENANT_ID', 'common')

        if env_client_id:
            self.logger.info("Loading Azure credentials from environment variables")
            return env_client_id, env_tenant_id

        # Priority 2: OAuth config file
        # Try to find config file (works both in dev and PyInstaller bundle)
        config_paths = [
            Path(self.OAUTH_CONFIG_FILE),  # Development path
            Path(sys._MEIPASS) / self.OAUTH_CONFIG_FILE if getattr(sys, 'frozen', False) else None,  # PyInstaller bundle
        ]

        for config_path in config_paths:
            if config_path and config_path.exists():
                try:
                    with open(config_path, 'r', encoding='utf-8') as f:
                        config = json.load(f)

                    if config.get('enabled', True):
                        client_id = config.get('azure_client_id')
                        tenant_id = config.get('azure_tenant_id', 'common')

                        if client_id and client_id != 'TU_AZURE_CLIENT_ID_AQUI':
                            self.logger.info(f"Loading Azure credentials from config file: {config_path}")
                            return client_id, tenant_id

                except json.JSONDecodeError as e:
                    self.logger.error(f"Error parsing OAuth config file: {e}")
                except Exception as e:
                    self.logger.error(f"Error reading OAuth config file: {e}")

        # No credentials found
        self.logger.warning("No Azure credentials found in environment or config file")
        return None, tenant_id

    def _load_token_cache(self) -> msal.SerializableTokenCache:
        """Load token cache from file if it exists

        The token cache stores access tokens, refresh tokens, and metadata
        to avoid repeated authentication. Tokens typically last 60-90 days.

        Returns:
            SerializableTokenCache: MSAL token cache object
        """
        cache = msal.SerializableTokenCache()

        cache_path = Path(self.TOKEN_CACHE_FILE)
        if cache_path.exists():
            try:
                cache_data = cache_path.read_text()
                cache.deserialize(cache_data)
                self.logger.info("OAuth token cache loaded successfully")
            except Exception as e:
                self.logger.warning(f"Failed to load token cache: {e}")

        return cache

    def _save_token_cache(self) -> None:
        """Save token cache to file for future use

        This persists tokens across application restarts, eliminating the need
        for users to re-authenticate on every execution.
        """
        if self.token_cache.has_state_changed:
            try:
                cache_path = Path(self.TOKEN_CACHE_FILE)
                cache_path.write_text(self.token_cache.serialize())
                self.logger.info("OAuth token cache saved successfully")
            except Exception as e:
                self.logger.error(f"Failed to save token cache: {e}")

    def _acquire_token_interactive(self, email: str) -> Optional[str]:
        """Acquire access token using Device Code Flow

        Device Code Flow Process:
        1. Request device code from Azure AD
        2. Display verification URL and user code to user
        3. User navigates to URL in browser
        4. User enters code and authenticates
        5. App polls Azure AD until user completes authentication
        6. Azure AD returns access token

        Args:
            email: User's email address (used as login hint)

        Returns:
            Access token string if successful, None otherwise
        """
        self.logger.info("Starting OAuth 2.0 Device Code Flow...")

        # Check if we have a cached token first
        accounts = self.app.get_accounts(username=email)
        if accounts:
            self.logger.info(f"Found cached account for {email}")
            result = self.app.acquire_token_silent(
                scopes=self.SCOPES,
                account=accounts[0]
            )
            if result and "access_token" in result:
                self.logger.info("Using cached access token")
                self._save_token_cache()
                return result["access_token"]

        # No cached token, initiate device flow
        self.logger.info("No cached token found, initiating device flow...")

        try:
            # Initiate device flow
            flow = self.app.initiate_device_flow(scopes=self.SCOPES)

            if "user_code" not in flow:
                raise ValueError(
                    f"Failed to create device flow. Error: {flow.get('error')}"
                    f"\nDescription: {flow.get('error_description')}"
                )

            # Display instructions to user
            print("\n" + "="*70)
            print("  AUTENTICACIÓN OAUTH 2.0 REQUERIDA")
            print("="*70)
            print(f"\n{flow['message']}")
            print("\nInstrucciones:")
            print("1. Abre tu navegador y visita la URL mostrada arriba")
            print("2. Ingresa el código mostrado arriba")
            print(f"3. Inicia sesión con: {email}")
            print("4. Autoriza los permisos IMAP cuando se solicite")
            print("5. Regresa a esta aplicación")
            print("\n" + "="*70 + "\n")

            # Poll for token (blocks until user completes authentication)
            self.logger.info("Waiting for user to complete authentication...")
            result = self.app.acquire_token_by_device_flow(flow)

            if "access_token" in result:
                self.logger.info("✓ Authentication successful!")
                self._save_token_cache()
                print("\n✓ Autenticación exitosa. El token se ha guardado para futuras sesiones.\n")
                return result["access_token"]
            else:
                error = result.get("error", "unknown")
                error_desc = result.get("error_description", "No description")
                self.logger.error(f"Authentication failed: {error} - {error_desc}")
                print(f"\n✗ Error de autenticación: {error}")
                print(f"  Descripción: {error_desc}\n")
                return None

        except Exception as e:
            self.logger.error(f"Error during device flow: {e}")
            print(f"\n✗ Error durante autenticación OAuth: {e}\n")
            return None

    def connect(self, email_addr: str, password: str, imap_server: str) -> bool:
        """Connect to IMAP server using OAuth 2.0

        Note: The 'password' parameter is ignored but kept for interface compatibility.
        OAuth 2.0 uses access tokens instead of passwords.

        Args:
            email_addr: User's email address
            password: Ignored (kept for interface compatibility)
            imap_server: IMAP server hostname (e.g., outlook.office365.com)

        Returns:
            True if connection successful, False otherwise

        Raises:
            ConnectionError: If connection or authentication fails
        """
        try:
            self.logger.info(f"Connecting to {imap_server} using OAuth 2.0...")

            # Acquire OAuth 2.0 access token
            access_token = self._acquire_token_interactive(email_addr)

            if not access_token:
                raise ConnectionError(
                    "Failed to acquire OAuth 2.0 access token. "
                    "Please check your internet connection and try again."
                )

            # Connect to IMAP server
            self.imap = imaplib.IMAP4_SSL(imap_server, 993)

            # Enable debug if needed (shows IMAP conversation)
            # self.imap.debug = 4

            # Authenticate using XOAUTH2
            # Format: user=<email>\x01auth=Bearer <token>\x01\x01
            auth_string = f"user={email_addr}\x01auth=Bearer {access_token}\x01\x01"
            auth_bytes = auth_string.encode('ascii')

            self.logger.info("Authenticating with XOAUTH2...")
            self.imap.authenticate('XOAUTH2', lambda x: auth_bytes)

            # Select INBOX
            self.imap.select('INBOX')

            self.logger.info(f"✓ Successfully connected to {imap_server} as {email_addr}")
            return True

        except imaplib.IMAP4.error as e:
            error_msg = str(e)
            self.logger.error(f"IMAP authentication error: {error_msg}")

            # Provide helpful error messages
            raise ConnectionError(
                f"Failed to authenticate with IMAP server: {error_msg}\n\n"
                "Posibles soluciones:\n"
                "1. Verifica que IMAP esté habilitado en tu cuenta de Outlook:\n"
                "   Outlook Web > Configuración > Ver toda la configuración > "
                "Correo > Sincronizar correo > IMAP\n"
                "2. Asegúrate de que la cuenta tiene permisos para usar OAuth 2.0\n"
                "3. Verifica que completaste el flujo de autenticación en el navegador\n"
                "4. Si el error persiste, elimina el archivo de cache: "
                f"{self.TOKEN_CACHE_FILE}\n"
            )

        except Exception as e:
            self.logger.error(f"Connection error: {e}")
            raise ConnectionError(
                f"Failed to connect to IMAP server: {str(e)}\n"
                f"Servidor: {imap_server}:993\n"
                f"Email: {email_addr}\n"
                "Ejecuta 'python test_oauth_pulgarin.py' para diagnosticar"
            )

    def search_emails(self, search_criteria: str) -> List[str]:
        """Search emails by criteria

        Args:
            search_criteria: IMAP search criteria (e.g., 'UNSEEN SUBJECT "PULGARIN"')

        Returns:
            List of email IDs matching the criteria

        Raises:
            ConnectionError: If not connected to server
            RuntimeError: If search fails
        """
        if not self.imap:
            raise ConnectionError("Not connected to IMAP server")

        try:
            status, messages = self.imap.search(None, search_criteria)

            if status != 'OK':
                return []

            email_ids = messages[0].split()
            self.logger.info(f"Found {len(email_ids)} emails matching criteria")
            return [msg_id.decode() for msg_id in email_ids]

        except Exception as e:
            self.logger.error(f"Error searching emails: {e}")
            raise RuntimeError(f"Error searching emails: {str(e)}")

    def fetch_email(self, email_id: str) -> Tuple[bytes, dict]:
        """Fetch email by ID

        Args:
            email_id: Email ID to fetch

        Returns:
            Tuple of (email_body_bytes, email_info_dict)

        Raises:
            ConnectionError: If not connected to server
            RuntimeError: If fetch fails
        """
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
            self.logger.error(f"Error fetching email {email_id}: {e}")
            raise RuntimeError(f"Error fetching email {email_id}: {str(e)}")

    def extract_attachments(self, email_data: bytes) -> List[Tuple[str, bytes]]:
        """Extract attachments from email

        Args:
            email_data: Raw email data bytes

        Returns:
            List of tuples (filename, content_bytes)

        Raises:
            RuntimeError: If extraction fails
        """
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

            self.logger.info(f"Extracted {len(attachments)} attachments")

        except Exception as e:
            self.logger.error(f"Error extracting attachments: {e}")
            raise RuntimeError(f"Error extracting attachments: {str(e)}")

        return attachments

    def disconnect(self) -> None:
        """Disconnect from IMAP server"""
        if self.imap:
            try:
                self.imap.close()
                self.imap.logout()
                self.logger.info("Disconnected from IMAP server")
            except:
                pass
            finally:
                self.imap = None

    def _decode_header(self, header_value: str) -> str:
        """Decode email header

        Args:
            header_value: Raw header value (may be encoded)

        Returns:
            Decoded string
        """
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
