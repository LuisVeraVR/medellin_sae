"""Configuration Data Transfer Objects - Application Layer"""
from dataclasses import dataclass
from typing import Dict, Any, List


@dataclass
class ClientConfigDTO:
    """DTO for client configuration"""

    id: str
    name: str
    enabled: bool
    email_config: Dict[str, Any]
    xml_config: Dict[str, Any]
    output_config: Dict[str, Any]


@dataclass
class AppConfigDTO:
    """DTO for application configuration"""

    github_repo_url: str
    check_updates_on_startup: bool
    auto_update_enabled: bool
    log_level: str
    output_directory: str
    clients: List[ClientConfigDTO]
