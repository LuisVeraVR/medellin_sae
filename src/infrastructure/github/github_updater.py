"""GitHub Update Repository Implementation - Infrastructure Layer"""
import requests
import os
import sys
import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import Optional, Tuple
from packaging import version
from ...domain.repositories.update_repository import UpdateRepository


class GitHubUpdater(UpdateRepository):
    """GitHub-based update implementation"""

    def __init__(self, version_file: str = "version.txt"):
        self.version_file = version_file

    def get_current_version(self) -> str:
        """Get current application version"""
        try:
            version_path = Path(self.version_file)
            if version_path.exists():
                return version_path.read_text().strip()
            else:
                return "v0.0.0"
        except:
            return "v0.0.0"

    def check_for_updates(self, current_version: str, repo_url: str) -> Optional[Tuple[str, str]]:
        """
        Check for updates from GitHub releases
        Returns: (version, download_url) if update available, None otherwise
        """
        try:
            # Extract owner and repo from URL
            # Expected format: https://github.com/owner/repo
            parts = repo_url.rstrip('/').split('/')
            owner = parts[-2]
            repo = parts[-1]

            # Get latest release from GitHub API
            api_url = f"https://api.github.com/repos/{owner}/{repo}/releases/latest"

            response = requests.get(api_url, timeout=10)

            if response.status_code != 200:
                return None

            release_data = response.json()
            latest_version = release_data.get('tag_name', '')

            # Remove 'v' prefix if present for comparison
            current_ver = current_version.lstrip('v')
            latest_ver = latest_version.lstrip('v')

            # Compare versions
            if version.parse(latest_ver) > version.parse(current_ver):
                # Find download URL for the asset
                assets = release_data.get('assets', [])

                # Look for .exe or .zip file
                download_url = None
                for asset in assets:
                    name = asset.get('name', '').lower()
                    if name.endswith('.exe') or name.endswith('.zip'):
                        download_url = asset.get('browser_download_url')
                        break

                # If no assets, use zipball
                if not download_url:
                    download_url = release_data.get('zipball_url')

                return (latest_version, download_url)

            return None

        except Exception as e:
            raise RuntimeError(f"Error checking for updates: {str(e)}")

    def download_update(self, download_url: str, destination: str) -> bool:
        """Download update file"""
        try:
            response = requests.get(download_url, stream=True, timeout=30)

            if response.status_code != 200:
                return False

            # Save to destination
            dest_path = Path(destination)
            dest_path.parent.mkdir(parents=True, exist_ok=True)

            with open(dest_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            return True

        except Exception as e:
            raise RuntimeError(f"Error downloading update: {str(e)}")

    def apply_update(self, update_file: str) -> bool:
        """Apply downloaded update"""
        try:
            update_path = Path(update_file)

            if not update_path.exists():
                return False

            # Determine if it's a zip or exe
            if update_path.suffix.lower() == '.zip':
                return self._apply_zip_update(update_path)
            elif update_path.suffix.lower() == '.exe':
                return self._apply_exe_update(update_path)
            else:
                return False

        except Exception as e:
            raise RuntimeError(f"Error applying update: {str(e)}")

    def _apply_zip_update(self, zip_path: Path) -> bool:
        """Apply update from ZIP file"""
        try:
            # Create temporary directory
            temp_dir = Path(tempfile.mkdtemp())

            # Extract ZIP
            with zipfile.ZipFile(zip_path, 'r') as zf:
                zf.extractall(temp_dir)

            # Find the executable or main files
            app_dir = Path(sys.argv[0]).parent

            # Copy files from temp to app directory
            for item in temp_dir.rglob('*'):
                if item.is_file():
                    relative_path = item.relative_to(temp_dir)
                    dest_path = app_dir / relative_path
                    dest_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(item, dest_path)

            # Clean up
            shutil.rmtree(temp_dir)

            return True

        except Exception as e:
            raise RuntimeError(f"Error applying ZIP update: {str(e)}")

    def _apply_exe_update(self, exe_path: Path) -> bool:
        """Apply update from EXE file"""
        try:
            # Get current executable path
            current_exe = Path(sys.argv[0])

            # Backup current executable
            backup_path = current_exe.with_suffix('.bak')
            if current_exe.exists():
                shutil.copy2(current_exe, backup_path)

            # Replace with new executable
            shutil.copy2(exe_path, current_exe)

            # Remove backup if successful
            if backup_path.exists():
                backup_path.unlink()

            return True

        except Exception as e:
            # Restore backup if failed
            backup_path = Path(sys.argv[0]).with_suffix('.bak')
            if backup_path.exists():
                shutil.copy2(backup_path, sys.argv[0])
                backup_path.unlink()

            raise RuntimeError(f"Error applying EXE update: {str(e)}")
