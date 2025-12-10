"""OAuth 2.0 Authentication Dialog - Presentation Layer"""
import webbrowser
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QProgressBar, QMessageBox
)
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtGui import QFont
import logging


class OAuth2AuthWorker(QThread):
    """Worker thread for OAuth 2.0 authentication"""

    # Signals
    device_code_received = pyqtSignal(dict)  # Emits device code info
    authentication_success = pyqtSignal(str)  # Emits access token
    authentication_failed = pyqtSignal(str)  # Emits error message
    status_update = pyqtSignal(str)  # Emits status messages

    def __init__(self, email: str, oauth_repo):
        super().__init__()
        self.email = email
        self.oauth_repo = oauth_repo
        self.logger = logging.getLogger(__name__)

    def run(self):
        """Execute OAuth authentication in background"""
        try:
            self.status_update.emit("Iniciando autenticación OAuth 2.0...")

            # Check for cached token first
            accounts = self.oauth_repo.app.get_accounts(username=self.email)
            if accounts:
                self.status_update.emit("Encontrada cuenta en cache, verificando...")
                result = self.oauth_repo.app.acquire_token_silent(
                    scopes=self.oauth_repo.SCOPES,
                    account=accounts[0]
                )
                if result and "access_token" in result:
                    self.status_update.emit("✓ Token en cache válido")
                    self.oauth_repo._save_token_cache()
                    self.authentication_success.emit(result["access_token"])
                    return

            # No cached token, initiate device flow
            self.status_update.emit("Iniciando flujo de autenticación...")

            flow = self.oauth_repo.app.initiate_device_flow(scopes=self.oauth_repo.SCOPES)

            if "user_code" not in flow:
                error = flow.get('error', 'Unknown error')
                error_desc = flow.get('error_description', 'No description')
                self.authentication_failed.emit(f"{error}: {error_desc}")
                return

            # Emit device code info
            self.device_code_received.emit(flow)

            # Poll for token
            self.status_update.emit("Esperando autenticación del usuario...")
            result = self.oauth_repo.app.acquire_token_by_device_flow(flow)

            if "access_token" in result:
                self.status_update.emit("✓ Autenticación exitosa")
                self.oauth_repo._save_token_cache()
                self.authentication_success.emit(result["access_token"])
            else:
                error = result.get("error", "unknown")
                error_desc = result.get("error_description", "No description")
                self.authentication_failed.emit(f"{error}: {error_desc}")

        except Exception as e:
            self.logger.error(f"Error in OAuth worker: {e}")
            self.authentication_failed.emit(str(e))


class OAuth2Dialog(QDialog):
    """Dialog for OAuth 2.0 device code flow authentication"""

    authentication_success = pyqtSignal(str)  # Emits email on success

    def __init__(self, email: str, oauth_repo, parent=None):
        super().__init__(parent)
        self.email = email
        self.oauth_repo = oauth_repo
        self.access_token = None

        self.setWindowTitle("Autenticación OAuth 2.0 - Office 365")
        self.setMinimumSize(600, 500)
        self.setModal(True)

        self._init_ui()
        self._start_authentication()

    def _init_ui(self):
        """Initialize UI components"""
        layout = QVBoxLayout()

        # Title
        title_label = QLabel("<h2>🔐 Autenticación Office 365</h2>")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # Email info
        email_label = QLabel(f"<b>Email:</b> {self.email}")
        email_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(email_label)

        # Instructions
        instructions = QLabel(
            "<b>Instrucciones:</b><br>"
            "1. Tu navegador se abrirá automáticamente<br>"
            "2. Ingresa el código que aparece abajo<br>"
            "3. Inicia sesión con tu cuenta de Office 365<br>"
            "4. Autoriza los permisos cuando se solicite<br>"
            "5. Regresa a esta ventana<br>"
        )
        instructions.setWordWrap(True)
        layout.addWidget(instructions)

        # Device code display
        code_group_layout = QVBoxLayout()

        self.code_label = QLabel("<h1 style='color: #0078D4;'>-</h1>")
        self.code_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.code_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        code_group_layout.addWidget(self.code_label)

        # URL display
        self.url_label = QLabel("<a href='#'>-</a>")
        self.url_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.url_label.setOpenExternalLinks(False)
        self.url_label.linkActivated.connect(self._open_browser)
        code_group_layout.addWidget(self.url_label)

        # Copy button
        self.copy_button = QPushButton("📋 Copiar Código")
        self.copy_button.clicked.connect(self._copy_code)
        self.copy_button.setEnabled(False)
        code_group_layout.addWidget(self.copy_button)

        # Open browser button
        self.browser_button = QPushButton("🌐 Abrir Navegador")
        self.browser_button.clicked.connect(self._open_browser)
        self.browser_button.setEnabled(False)
        code_group_layout.addWidget(self.browser_button)

        layout.addLayout(code_group_layout)

        # Status text
        status_label = QLabel("<b>Estado:</b>")
        layout.addWidget(status_label)

        self.status_text = QTextEdit()
        self.status_text.setReadOnly(True)
        self.status_text.setMaximumHeight(120)
        layout.addWidget(self.status_text)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Indeterminate
        layout.addWidget(self.progress_bar)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.cancel_button = QPushButton("Cancelar")
        self.cancel_button.clicked.connect(self._on_cancel)
        button_layout.addWidget(self.cancel_button)

        self.close_button = QPushButton("Cerrar")
        self.close_button.clicked.connect(self.accept)
        self.close_button.setEnabled(False)
        button_layout.addWidget(self.close_button)

        layout.addLayout(button_layout)

        self.setLayout(layout)

    def _start_authentication(self):
        """Start the OAuth authentication process"""
        # Create worker thread
        self.worker = OAuth2AuthWorker(self.email, self.oauth_repo)
        self.worker.device_code_received.connect(self._on_device_code_received)
        self.worker.authentication_success.connect(self._on_authentication_success)
        self.worker.authentication_failed.connect(self._on_authentication_failed)
        self.worker.status_update.connect(self._on_status_update)
        self.worker.finished.connect(self._on_worker_finished)

        self.worker.start()

    def _on_device_code_received(self, flow: dict):
        """Handle device code received"""
        self.flow = flow

        # Extract info
        user_code = flow.get('user_code', '')
        verification_uri = flow.get('verification_uri', '')

        # Update UI
        self.code_label.setText(f"<h1 style='color: #0078D4;'>{user_code}</h1>")
        self.url_label.setText(
            f"<a href='{verification_uri}' style='font-size: 14px;'>{verification_uri}</a>"
        )

        self.copy_button.setEnabled(True)
        self.browser_button.setEnabled(True)

        self._add_status(f"✓ Código recibido: {user_code}")
        self._add_status(f"✓ URL: {verification_uri}")
        self._add_status("")
        self._add_status("Abriendo navegador automáticamente...")

        # Auto-open browser
        self._open_browser()

    def _on_authentication_success(self, access_token: str):
        """Handle successful authentication"""
        self.access_token = access_token

        self._add_status("")
        self._add_status("=" * 50)
        self._add_status("✓ ¡AUTENTICACIÓN EXITOSA!")
        self._add_status("=" * 50)
        self._add_status("")
        self._add_status("Tu cuenta ha sido autenticada correctamente.")
        self._add_status("El token se ha guardado para futuras sesiones.")
        self._add_status("")
        self._add_status("Puedes cerrar esta ventana.")

        self.progress_bar.setRange(0, 1)
        self.progress_bar.setValue(1)

        self.cancel_button.setEnabled(False)
        self.close_button.setEnabled(True)

        # Emit success signal
        self.authentication_success.emit(self.email)

        # Show success message
        QMessageBox.information(
            self,
            "Autenticación Exitosa",
            f"Has autenticado correctamente con la cuenta:\n{self.email}\n\n"
            "El token ha sido guardado para futuras sesiones."
        )

    def _on_authentication_failed(self, error: str):
        """Handle authentication failure"""
        self._add_status("")
        self._add_status("=" * 50)
        self._add_status("✗ ERROR DE AUTENTICACIÓN")
        self._add_status("=" * 50)
        self._add_status("")
        self._add_status(f"Error: {error}")
        self._add_status("")
        self._add_status("Por favor, intenta nuevamente.")

        self.progress_bar.setRange(0, 1)
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("Error")

        self.cancel_button.setText("Cerrar")
        self.close_button.setEnabled(True)

        # Show error message
        QMessageBox.critical(
            self,
            "Error de Autenticación",
            f"No se pudo completar la autenticación:\n\n{error}\n\n"
            "Por favor, verifica tu conexión a internet e intenta nuevamente."
        )

    def _on_status_update(self, message: str):
        """Handle status update"""
        self._add_status(message)

    def _on_worker_finished(self):
        """Handle worker thread finished"""
        pass

    def _add_status(self, message: str):
        """Add a status message"""
        self.status_text.append(message)
        # Auto-scroll to bottom
        scrollbar = self.status_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def _open_browser(self):
        """Open browser with verification URL"""
        if hasattr(self, 'flow'):
            url = self.flow.get('verification_uri', '')
            if url:
                try:
                    webbrowser.open(url)
                    self._add_status("✓ Navegador abierto")
                except Exception as e:
                    self._add_status(f"✗ Error abriendo navegador: {e}")

    def _copy_code(self):
        """Copy device code to clipboard"""
        if hasattr(self, 'flow'):
            code = self.flow.get('user_code', '')
            if code:
                from PyQt6.QtWidgets import QApplication
                clipboard = QApplication.clipboard()
                clipboard.setText(code)
                self._add_status("✓ Código copiado al portapapeles")
                QMessageBox.information(self, "Código Copiado", f"El código {code} ha sido copiado al portapapeles.")

    def _on_cancel(self):
        """Handle cancel button"""
        if hasattr(self, 'worker') and self.worker.isRunning():
            reply = QMessageBox.question(
                self,
                "Cancelar Autenticación",
                "¿Estás seguro de que deseas cancelar la autenticación?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                self.worker.terminate()
                self.reject()
        else:
            self.reject()

    def get_access_token(self) -> str:
        """Get the access token if authentication was successful"""
        return self.access_token
