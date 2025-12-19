"""Somex API Client - Infrastructure Layer"""
import requests
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta


class SomexApiClient:
    """Client for Somex API to fetch invoice data"""

    BASE_URL = "https://somexapp.com/ApiAutoAccess/SomexAutoAccess"
    AUTH_ENDPOINT = "/Auth/login"
    INVOICE_ENDPOINT = "/FacturasBolsaAgro"

    def __init__(
        self,
        username: str = "Somex@automatiza.co",
        password: str = "04FD480CC15DE02F07297B6BD2E473C9",
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize Somex API client

        Args:
            username: API username
            password: API password (hash)
            logger: Logger instance
        """
        self.username = username
        self.password = password
        self.logger = logger or logging.getLogger(__name__)
        self.token: Optional[str] = None
        self.token_expiry: Optional[datetime] = None

    def _is_token_valid(self) -> bool:
        """Check if current token is still valid"""
        if not self.token or not self.token_expiry:
            return False

        # Consider token expired 5 minutes before actual expiry
        return datetime.now() < (self.token_expiry - timedelta(minutes=5))

    def authenticate(self) -> bool:
        """
        Authenticate with Somex API and get token

        Returns:
            True if authentication successful, False otherwise
        """
        try:
            # Check if we already have a valid token
            if self._is_token_valid():
                self.logger.info("Using cached authentication token")
                return True

            url = f"{self.BASE_URL}{self.AUTH_ENDPOINT}"
            payload = {
                "username": self.username,
                "password": self.password
            }

            self.logger.info(f"Authenticating with Somex API: {url}")

            response = requests.post(
                url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )

            response.raise_for_status()

            data = response.json()

            # Extract token from response
            # The token might be in different fields depending on API response structure
            # Common patterns: 'token', 'access_token', 'Token', 'AccessToken'
            self.token = (
                data.get('token') or
                data.get('access_token') or
                data.get('Token') or
                data.get('AccessToken')
            )

            if not self.token:
                self.logger.error(f"No token found in API response: {data}")
                return False

            # Set token expiry (default to 1 hour if not provided)
            expires_in = data.get('expires_in', 3600)
            self.token_expiry = datetime.now() + timedelta(seconds=expires_in)

            self.logger.info("Successfully authenticated with Somex API")
            return True

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error authenticating with Somex API: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error during authentication: {e}")
            return False

    def get_invoice_data(self, invoice_number: str) -> Optional[List[Dict[str, Any]]]:
        """
        Get invoice data from Somex API

        Args:
            invoice_number: Invoice number (e.g., "2B-285138")

        Returns:
            List of invoice line items or None if error
        """
        try:
            # Ensure we're authenticated
            if not self.authenticate():
                self.logger.error("Failed to authenticate before getting invoice data")
                return None

            url = f"{self.BASE_URL}{self.INVOICE_ENDPOINT}/{invoice_number}"

            headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json"
            }

            self.logger.info(f"Fetching invoice data from Somex API: {url}")

            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()

            data = response.json()

            # The API returns a list of items
            if isinstance(data, list):
                self.logger.info(
                    f"Successfully fetched {len(data)} items for invoice {invoice_number}"
                )
                return data
            elif isinstance(data, dict):
                # If single item, wrap in list
                self.logger.info(f"Successfully fetched 1 item for invoice {invoice_number}")
                return [data]
            else:
                self.logger.error(f"Unexpected API response format: {type(data)}")
                return None

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                self.logger.warning(
                    f"Invoice {invoice_number} not found in Somex API (404)"
                )
            else:
                self.logger.error(f"HTTP error fetching invoice {invoice_number}: {e}")
            return None
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error fetching invoice {invoice_number}: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error fetching invoice {invoice_number}: {e}")
            return None

    def get_item_by_reference(
        self,
        invoice_number: str,
        referencia: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get a specific item from invoice by reference

        Args:
            invoice_number: Invoice number
            referencia: Product reference code

        Returns:
            Item data or None if not found
        """
        invoice_data = self.get_invoice_data(invoice_number)

        if not invoice_data:
            return None

        # Find item with matching reference
        for item in invoice_data:
            if item.get('referencia') == referencia:
                self.logger.info(
                    f"Found item with reference {referencia} in invoice {invoice_number}"
                )
                return item

        self.logger.warning(
            f"Item with reference {referencia} not found in invoice {invoice_number}"
        )
        return None
