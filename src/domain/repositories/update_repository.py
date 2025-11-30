"""Update Repository Interface - Domain Layer"""
from abc import ABC, abstractmethod
from typing import Optional, Tuple


class UpdateRepository(ABC):
    """Abstract interface for application update operations"""

    @abstractmethod
    def check_for_updates(self, current_version: str, repo_url: str) -> Optional[Tuple[str, str]]:
        """
        Check for updates from GitHub releases
        Returns: (version, download_url) if update available, None otherwise
        """
        pass

    @abstractmethod
    def download_update(self, download_url: str, destination: str) -> bool:
        """Download update file"""
        pass

    @abstractmethod
    def apply_update(self, update_file: str) -> bool:
        """Apply downloaded update"""
        pass

    @abstractmethod
    def get_current_version(self) -> str:
        """Get current application version"""
        pass
