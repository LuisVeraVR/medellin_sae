"""Configuration Service - Application Layer"""
import json
import logging
from pathlib import Path
from typing import List, Optional
from src.domain.entities.client import Client
from src.dto.config_dto import AppConfigDTO, ClientConfigDTO


class ConfigService:
    """Service for configuration management"""

    def __init__(self, config_dir: str = "config", logger: Optional[logging.Logger] = None):
        self.config_dir = Path(config_dir)
        self.logger = logger or logging.getLogger(__name__)
        self.config_dir.mkdir(parents=True, exist_ok=True)

    def load_clients(self) -> List[Client]:
        """Load client configurations"""
        try:
            clients_file = self.config_dir / "clients.json"

            if not clients_file.exists():
                self.logger.warning("clients.json not found, creating default")
                self._create_default_clients_config()

            with open(clients_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            clients = []
            for client_data in data.get('clients', []):
                client = Client(
                    id=client_data['id'],
                    name=client_data['name'],
                    enabled=client_data['enabled'],
                    email_config=client_data['email_config'],
                    xml_config=client_data['xml_config'],
                    output_config=client_data['output_config']
                )
                clients.append(client)

            self.logger.info(f"Loaded {len(clients)} client configurations")
            return clients

        except Exception as e:
            self.logger.error(f"Error loading clients: {str(e)}")
            return []

    def load_app_config(self) -> dict:
        """Load application configuration"""
        try:
            config_file = self.config_dir / "app_config.json"

            if not config_file.exists():
                self.logger.warning("app_config.json not found, creating default")
                self._create_default_app_config()

            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)

            self.logger.info("Loaded application configuration")
            return config

        except Exception as e:
            self.logger.error(f"Error loading app config: {str(e)}")
            return self._get_default_app_config()

    def _create_default_clients_config(self) -> None:
        """Create default clients configuration"""
        default_config = {
            "clients": [
                {
                    "id": "triple_a",
                    "name": "Comercializadora Triple A",
                    "enabled": True,
                    "email_config": {
                        "search_criteria": "(UNSEEN SUBJECT \"COMERCIALIZADORA TRIPLE A\")",
                        "imap_server": "outlook.office365.com"
                    },
                    "xml_config": {
                        "format": "ubl_2.1"
                    },
                    "output_config": {
                        "csv_delimiter": ";",
                        "decimal_separator": ",",
                        "decimal_places": 5
                    }
                }
            ]
        }

        clients_file = self.config_dir / "clients.json"
        with open(clients_file, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, indent=2, ensure_ascii=False)

    def _create_default_app_config(self) -> None:
        """Create default application configuration"""
        default_config = self._get_default_app_config()

        config_file = self.config_dir / "app_config.json"
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, indent=2, ensure_ascii=False)

    def _get_default_app_config(self) -> dict:
        """Get default application configuration"""
        return {
            "github_repo_url": "https://github.com/LuisVeraVR/medellin_sae",
            "check_updates_on_startup": True,
            "auto_update_enabled": True,
            "log_level": "INFO",
            "output_directory": "output"
        }
