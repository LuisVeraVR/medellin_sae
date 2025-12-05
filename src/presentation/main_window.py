"""Main Window - Presentation Layer"""
import os
import logging
import tempfile
from pathlib import Path
from typing import Dict, List
from PyQt6.QtWidgets import (
    QMainWindow, QTabWidget, QMessageBox, QStatusBar,
    QSystemTrayIcon, QMenu, QApplication
)
from PyQt6.QtCore import QThread, pyqtSignal, QSettings
from PyQt6.QtGui import QIcon, QAction
from dotenv import load_dotenv

from src.domain.entities.client import Client
from src.domain.entities.processing_result import ProcessingResult
from src.domain.use_cases.process_invoices_use_case import ProcessInvoicesUseCase
from src.domain.use_cases.check_updates_use_case import CheckUpdatesUseCase
from src.infrastructure.email.imap_email_repository import IMAPEmailRepository
from src.infrastructure.email.oauth2_imap_repository import OAuth2IMAPRepository
from src.infrastructure.xml.ubl_xml_parser import UBLXMLParser
from src.infrastructure.database.sqlite_repository import SQLiteRepository
from src.infrastructure.csv.csv_exporter import CSVExporter
from src.infrastructure.github.github_updater import GitHubUpdater
from src.application.services.config_service import ConfigService
from src.presentation.widgets.client_tab import ClientTab
from src.presentation.widgets.config_tab import ConfigTab
from src.presentation.widgets.logs_tab import LogsTab
from src.presentation.widgets.somex_tab import SomexTab


class ProcessingWorker(QThread):
    """Worker thread for invoice processing"""

    finished = pyqtSignal(ProcessingResult)
    log_message = pyqtSignal(str, str)  # level, message

    def __init__(
        self,
        client: Client,
        email: str,
        password: str,
        output_dir: str,
        use_case: ProcessInvoicesUseCase,
        logger: logging.Logger,
        allow_reprocess: bool = False
    ):
        super().__init__()
        self.client = client
        self.email = email
        self.password = password
        self.output_dir = output_dir
        self.use_case = use_case
        self.logger = logger
        self.allow_reprocess = allow_reprocess

    def run(self) -> None:
        """Execute processing in background"""
        try:
            self.log_message.emit('INFO', f"Processing invoices for {self.client.name}")

            result = self.use_case.execute(
                self.client,
                self.email,
                self.password,
                self.output_dir,
                allow_reprocess=self.allow_reprocess
            )

            self.finished.emit(result)

        except Exception as e:
            self.logger.error(f"Error in processing worker: {str(e)}")
            result = ProcessingResult(
                client_id=self.client.id,
                timestamp=ProcessingResult.__init__.__defaults__[0]
            )
            result.add_error(str(e))
            self.finished.emit(result)


class MainWindow(QMainWindow):
    """Main application window"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Medellin SAE - Procesador de Facturas Electrónicas")
        self.setMinimumSize(1000, 700)

        # Load environment variables
        load_dotenv()

        # Initialize logging
        self._init_logging()

        # Initialize services
        self.config_service = ConfigService(logger=self.logger)
        self.app_config = self.config_service.load_app_config()
        self.clients = self.config_service.load_clients()

        # Initialize repositories (email_repo is created per-client in _on_processing_requested)
        self.xml_parser_repo = UBLXMLParser()
        self.csv_repo = CSVExporter()
        self.update_repo = GitHubUpdater()

        # Client tabs
        self.client_tabs: Dict[str, ClientTab] = {}
        self.workers: Dict[str, ProcessingWorker] = {}

        # Settings
        self.settings = QSettings('MedellinSAE', 'InvoiceProcessor')

        self._init_ui()
        self._restore_window_state()

        # Check for updates on startup
        if self.app_config.get('check_updates_on_startup', True):
            self._check_for_updates()

    def _init_logging(self) -> None:
        """Initialize logging configuration"""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / 'app.log'),
                logging.StreamHandler()
            ]
        )

        self.logger = logging.getLogger(__name__)

    def _init_ui(self) -> None:
        """Initialize UI components"""
        # Create tab widget
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # Create client tabs
        for client in self.clients:
            if client.enabled:
                client_tab = ClientTab(client, self.logger)
                client_tab.processing_requested.connect(self._on_processing_requested)
                self.client_tabs[client.id] = client_tab
                self.tabs.addTab(client_tab, client.name)

        # Create Somex SFTP tab
        self.somex_tab = SomexTab(self.logger)
        self.tabs.addTab(self.somex_tab, "Somex")

        # Create config tab
        self.config_tab = ConfigTab(self.app_config)
        self.config_tab.config_changed.connect(self._on_config_changed)
        self.tabs.addTab(self.config_tab, "Configuración")

        # Load credentials from env
        email = os.getenv('CORREAGRO_EMAIL', '')
        password = os.getenv('CORREAGRO_PASSWORD', '')
        self.config_tab.set_email_credentials(email, password)

        # Create logs tab
        self.logs_tab = LogsTab()
        self.tabs.addTab(self.logs_tab, "Logs")

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        version = self.update_repo.get_current_version()
        self.status_bar.showMessage(f"Versión: {version} | Listo")

        # System tray
        self._init_system_tray()

    def _init_system_tray(self) -> None:
        """Initialize system tray icon"""
        self.tray_icon = QSystemTrayIcon(self)

        # Create tray menu
        tray_menu = QMenu()

        show_action = QAction("Mostrar", self)
        show_action.triggered.connect(self.show)
        tray_menu.addAction(show_action)

        quit_action = QAction("Salir", self)
        quit_action.triggered.connect(QApplication.quit)
        tray_menu.addAction(quit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self._on_tray_activated)

        # Show tray icon
        # Note: Icon should be set when available
        self.tray_icon.show()

    def _on_tray_activated(self, reason) -> None:
        """Handle tray icon activation"""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show()

    def _on_processing_requested(self, client_id: str, allow_reprocess: bool = False) -> None:
        """Handle processing request from client tab"""
        # Get email credentials
        email, password = self.config_tab.get_email_credentials()

        if not email or not password:
            QMessageBox.warning(
                self,
                "Credenciales Faltantes",
                "Por favor configure el email y password en la pestaña Configuración"
            )
            return

        # Find client
        client = next((c for c in self.clients if c.id == client_id), None)
        if not client:
            return

        # Select appropriate email repository based on IMAP server
        # Office 365 (outlook.office365.com) requires OAuth 2.0
        # Other servers use basic authentication
        imap_server = client.email_config.get('imap_server', '')
        if 'office365' in imap_server or 'outlook.office365.com' in imap_server:
            email_repo = OAuth2IMAPRepository()
            self.logger.info(f"Using OAuth 2.0 authentication for {imap_server}")
        else:
            email_repo = IMAPEmailRepository()
            self.logger.info(f"Using basic authentication for {imap_server}")

        # Create database repository for client
        db_path = Path("data") / f"{client.id}_processed.db"
        db_repo = SQLiteRepository(str(db_path))

        # Create use case
        use_case = ProcessInvoicesUseCase(
            email_repo=email_repo,
            xml_parser_repo=self.xml_parser_repo,
            database_repo=db_repo,
            csv_repo=self.csv_repo,
            logger=self.logger
        )

        # Create output directory
        output_dir = Path(self.app_config.get('output_directory', 'output')) / client.id

        # Create and start worker
        worker = ProcessingWorker(
            client=client,
            email=email,
            password=password,
            output_dir=str(output_dir),
            use_case=use_case,
            logger=self.logger,
            allow_reprocess=allow_reprocess
        )

        worker.finished.connect(lambda result: self._on_processing_finished(client_id, result))
        worker.log_message.connect(self.logs_tab.add_log)

        self.workers[client_id] = worker
        worker.start()

        self.status_bar.showMessage(f"Procesando {client.name}...")

    def _on_processing_finished(self, client_id: str, result: ProcessingResult) -> None:
        """Handle processing completion"""
        client_tab = self.client_tabs.get(client_id)
        if client_tab:
            client_tab.update_stats(result)

        # Clean up worker
        if client_id in self.workers:
            del self.workers[client_id]

        self.status_bar.showMessage(f"Procesamiento completado | Versión: {self.update_repo.get_current_version()}")

    def _check_for_updates(self) -> None:
        """Check for application updates"""
        try:
            repo_url = self.app_config.get('github_repo_url', '')
            if not repo_url:
                return

            check_updates_use_case = CheckUpdatesUseCase(self.update_repo, self.logger)
            update_info = check_updates_use_case.execute(repo_url)

            if update_info:
                version, download_url = update_info

                reply = QMessageBox.question(
                    self,
                    "Actualización Disponible",
                    f"Nueva versión disponible: {version}\n\n¿Desea actualizar ahora?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )

                if reply == QMessageBox.StandardButton.Yes:
                    self._download_and_install_update(download_url)

        except Exception as e:
            self.logger.error(f"Error checking for updates: {str(e)}")

    def _download_and_install_update(self, download_url: str) -> None:
        """Download and install update"""
        try:
            temp_file = Path(tempfile.gettempdir()) / "medellin_sae_update.zip"

            self.status_bar.showMessage("Descargando actualización...")

            check_updates_use_case = CheckUpdatesUseCase(self.update_repo, self.logger)

            if check_updates_use_case.download_and_apply(download_url, str(temp_file)):
                QMessageBox.information(
                    self,
                    "Actualización Completada",
                    "La aplicación se reiniciará para aplicar la actualización."
                )

                # Restart application
                QApplication.quit()
                os.execl(sys.executable, sys.executable, *sys.argv)
            else:
                QMessageBox.warning(
                    self,
                    "Error",
                    "No se pudo instalar la actualización"
                )

        except Exception as e:
            self.logger.error(f"Error installing update: {str(e)}")
            QMessageBox.critical(
                self,
                "Error",
                f"Error al instalar actualización: {str(e)}"
            )

    def _on_config_changed(self, config: dict) -> None:
        """Handle configuration changes"""
        self.app_config.update(config)
        # TODO: Save config to file

    def _restore_window_state(self) -> None:
        """Restore window state from settings"""
        geometry = self.settings.value('geometry')
        if geometry:
            self.restoreGeometry(geometry)

    def closeEvent(self, event) -> None:
        """Handle window close event"""
        # Save window state
        self.settings.setValue('geometry', self.saveGeometry())

        # Stop all workers
        for worker in self.workers.values():
            worker.wait()

        event.accept()
