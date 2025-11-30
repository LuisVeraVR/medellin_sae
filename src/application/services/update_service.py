"""Update Service - Application Layer"""
import logging
from typing import Optional, Tuple
from ...domain.repositories.update_repository import UpdateRepository


class UpdateService:
    """Service for application update operations"""

    def __init__(self, update_repo: UpdateRepository, logger: logging.Logger):
        self.update_repo = update_repo
        self.logger = logger

    def check_for_updates(self, repo_url: str) -> Optional[Tuple[str, str]]:
        """
        Check for updates from GitHub
        Returns: (version, download_url) if available
        """
        try:
            current_version = self.update_repo.get_current_version()
            self.logger.info(f"Current version: {current_version}")

            update_info = self.update_repo.check_for_updates(current_version, repo_url)

            if update_info:
                version, url = update_info
                self.logger.info(f"Update available: {version}")
                return update_info
            else:
                self.logger.info("No updates available")
                return None

        except Exception as e:
            self.logger.error(f"Error checking for updates: {str(e)}")
            return None

    def download_and_install_update(self, download_url: str, temp_file: str) -> bool:
        """Download and install update"""
        try:
            self.logger.info("Downloading update...")

            if not self.update_repo.download_update(download_url, temp_file):
                self.logger.error("Failed to download update")
                return False

            self.logger.info("Installing update...")

            if not self.update_repo.apply_update(temp_file):
                self.logger.error("Failed to install update")
                return False

            self.logger.info("Update installed successfully")
            return True

        except Exception as e:
            self.logger.error(f"Error installing update: {str(e)}")
            return False

    def get_current_version(self) -> str:
        """Get current application version"""
        return self.update_repo.get_current_version()
