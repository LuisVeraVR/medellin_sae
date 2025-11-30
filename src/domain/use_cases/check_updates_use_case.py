"""Check Updates Use Case - Domain Layer"""
import logging
from typing import Optional, Tuple
from ..repositories.update_repository import UpdateRepository


class CheckUpdatesUseCase:
    """Use case for checking application updates"""

    def __init__(
        self,
        update_repo: UpdateRepository,
        logger: logging.Logger
    ):
        self.update_repo = update_repo
        self.logger = logger

    def execute(self, repo_url: str) -> Optional[Tuple[str, str]]:
        """
        Check for updates from GitHub
        Returns: (version, download_url) if update available, None otherwise
        """
        try:
            current_version = self.update_repo.get_current_version()
            self.logger.info(f"Current version: {current_version}")

            update_info = self.update_repo.check_for_updates(current_version, repo_url)

            if update_info:
                new_version, download_url = update_info
                self.logger.info(f"New version available: {new_version}")
                return update_info
            else:
                self.logger.info("No updates available")
                return None

        except Exception as e:
            self.logger.error(f"Error checking for updates: {str(e)}")
            return None

    def download_and_apply(self, download_url: str, destination: str) -> bool:
        """Download and apply update"""
        try:
            self.logger.info(f"Downloading update from {download_url}")

            if not self.update_repo.download_update(download_url, destination):
                self.logger.error("Failed to download update")
                return False

            self.logger.info("Applying update...")

            if not self.update_repo.apply_update(destination):
                self.logger.error("Failed to apply update")
                return False

            self.logger.info("Update applied successfully")
            return True

        except Exception as e:
            self.logger.error(f"Error downloading/applying update: {str(e)}")
            return False
