"""Configuration Tab Widget - Presentation Layer"""
import os
import json
import logging
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLineEdit,
    QPushButton, QLabel, QGroupBox, QCheckBox, QComboBox,
    QHBoxLayout, QMessageBox
)
from PyQt6.QtCore import pyqtSignal


class ConfigTab(QWidget):
    """Configuration tab widget"""

    config_changed = pyqtSignal(dict)
    oauth_authentication_requested = pyqtSignal(str)  # Emits email

    def __init__(self, config: dict, parent=None):
        super().__init__(parent)
        self.config = config
        self.logger = logging.getLogger(__name__)
        self._init_ui()

    def _init_ui(self) -> None:
        """Initialize UI components"""
        layout = QVBoxLayout()

        # GitHub settings
        github_group = QGroupBox("Configuración GitHub")
        github_layout = QFormLayout()

        self.repo_url_input = QLineEdit(self.config.get('github_repo_url', ''))
        github_layout.addRow("URL Repositorio:", self.repo_url_input)

        self.check_updates_checkbox = QCheckBox("Verificar actualizaciones al iniciar")
        self.check_updates_checkbox.setChecked(self.config.get('check_updates_on_startup', True))
        github_layout.addRow(self.check_updates_checkbox)

        self.auto_update_checkbox = QCheckBox("Actualización automática")
        self.auto_update_checkbox.setChecked(self.config.get('auto_update_enabled', True))
        github_layout.addRow(self.auto_update_checkbox)

        github_group.setLayout(github_layout)
        layout.addWidget(github_group)

        # Email settings
        email_group = QGroupBox("Configuración Email")
        email_layout = QFormLayout()

        # Email input
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("email@example.com")
        email_layout.addRow("Email:", self.email_input)

        # Password input (for basic auth)
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("Solo para autenticación básica")
        email_layout.addRow("Password:", self.password_input)

        # OAuth 2.0 section
        oauth_layout = QVBoxLayout()

        oauth_info = QLabel(
            "<b>Autenticación OAuth 2.0 (Office 365):</b><br>"
            "Para cuentas de Office 365, usa el botón abajo para autenticar de forma segura."
        )
        oauth_info.setWordWrap(True)
        oauth_layout.addWidget(oauth_info)

        # OAuth button layout
        oauth_button_layout = QHBoxLayout()

        self.oauth_button = QPushButton("🔐 Autenticar con Office 365 (OAuth 2.0)")
        self.oauth_button.setStyleSheet(
            "QPushButton { background-color: #0078D4; color: white; padding: 10px; font-weight: bold; }"
            "QPushButton:hover { background-color: #106EBE; }"
        )
        self.oauth_button.clicked.connect(self._on_oauth_authenticate)
        oauth_button_layout.addWidget(self.oauth_button)

        # Status label
        self.oauth_status_label = QLabel("")
        self.oauth_status_label.setWordWrap(True)
        oauth_button_layout.addWidget(self.oauth_status_label)

        oauth_button_layout.addStretch()
        oauth_layout.addLayout(oauth_button_layout)

        # Clear token button
        self.clear_token_button = QPushButton("🗑️ Borrar Token Guardado")
        self.clear_token_button.setStyleSheet("color: #D13438;")
        self.clear_token_button.clicked.connect(self._on_clear_token)
        oauth_layout.addWidget(self.clear_token_button)

        email_layout.addRow(oauth_layout)

        email_group.setLayout(email_layout)
        layout.addWidget(email_group)

        # Azure AD settings (for OAuth)
        azure_group = QGroupBox("Configuración Azure AD (OAuth 2.0)")
        azure_layout = QFormLayout()

        azure_info = QLabel(
            "<b>Credenciales de Azure para Office 365:</b><br>"
            "<i>Ingresa tu Client ID y Tenant ID manualmente. "
            "Se guardarán en config/oauth_config.json</i>"
        )
        azure_info.setWordWrap(True)
        azure_layout.addRow(azure_info)

        # Load current Azure config from file or env
        self._load_azure_config()

        # Client ID input
        self.azure_client_id_input = QLineEdit()
        self.azure_client_id_input.setText(self.azure_client_id)
        self.azure_client_id_input.setPlaceholderText("Ejemplo: 12345678-1234-1234-1234-123456789012")
        azure_layout.addRow("Client ID:", self.azure_client_id_input)

        # Tenant ID input
        self.azure_tenant_id_input = QLineEdit()
        self.azure_tenant_id_input.setText(self.azure_tenant_id)
        self.azure_tenant_id_input.setPlaceholderText("Ejemplo: common o tu-tenant-id")
        azure_layout.addRow("Tenant ID:", self.azure_tenant_id_input)

        # Save Azure config button
        self.save_azure_btn = QPushButton("💾 Guardar Credenciales Azure")
        self.save_azure_btn.setStyleSheet("background-color: #0078D4; color: white; padding: 5px;")
        self.save_azure_btn.clicked.connect(self._on_save_azure_config)
        azure_layout.addRow(self.save_azure_btn)

        azure_group.setLayout(azure_layout)
        layout.addWidget(azure_group)

        # Application settings
        app_group = QGroupBox("Configuración General")
        app_layout = QFormLayout()

        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(['DEBUG', 'INFO', 'WARNING', 'ERROR'])
        current_log_level = self.config.get('log_level', 'INFO')
        self.log_level_combo.setCurrentText(current_log_level)
        app_layout.addRow("Nivel de Log:", self.log_level_combo)

        self.output_dir_input = QLineEdit(self.config.get('output_directory', 'output'))
        app_layout.addRow("Directorio Output:", self.output_dir_input)

        app_group.setLayout(app_layout)
        layout.addWidget(app_group)

        # Save button
        save_btn = QPushButton("Guardar Configuración")
        save_btn.clicked.connect(self._on_save)
        layout.addWidget(save_btn)

        layout.addStretch()
        self.setLayout(layout)

        # Check OAuth status on init
        self._check_oauth_status()

    def _on_oauth_authenticate(self):
        """Handle OAuth authentication button click"""
        email = self.email_input.text().strip()

        if not email:
            QMessageBox.warning(
                self,
                "Email Requerido",
                "Por favor ingresa tu dirección de email de Office 365 antes de autenticar."
            )
            return

        # Check if Azure credentials are configured (from inputs or env)
        client_id = self.azure_client_id_input.text().strip() or os.getenv('AZURE_CLIENT_ID')
        if not client_id:
            QMessageBox.critical(
                self,
                "Configuración Faltante",
                "AZURE_CLIENT_ID no está configurado.\n\n"
                "Por favor:\n"
                "1. Ingresa tu Client ID de Azure en el campo de arriba\n"
                "2. Haz clic en 'Guardar Credenciales Azure'\n"
                "3. Luego intenta autenticar nuevamente"
            )
            return

        # Update environment variable if needed
        if not os.getenv('AZURE_CLIENT_ID'):
            os.environ['AZURE_CLIENT_ID'] = client_id
            if self.azure_tenant_id_input.text().strip():
                os.environ['AZURE_TENANT_ID'] = self.azure_tenant_id_input.text().strip()

        # Emit signal to main window to handle OAuth flow
        self.oauth_authentication_requested.emit(email)

    def _on_clear_token(self):
        """Handle clear token button click"""
        token_file = Path("data/oauth_token_cache.json")

        if not token_file.exists():
            QMessageBox.information(
                self,
                "Sin Token",
                "No hay token guardado para borrar."
            )
            return

        reply = QMessageBox.question(
            self,
            "Confirmar Borrado",
            "¿Estás seguro de que deseas borrar el token guardado?\n\n"
            "Tendrás que autenticarte nuevamente la próxima vez.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                token_file.unlink()
                self.oauth_status_label.setText("✓ Token borrado")
                self.oauth_status_label.setStyleSheet("color: orange;")
                QMessageBox.information(
                    self,
                    "Token Borrado",
                    "El token ha sido borrado exitosamente."
                )
                self.logger.info("OAuth token cache cleared")
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Error al borrar el token: {e}"
                )
                self.logger.error(f"Error clearing token: {e}")

    def _check_oauth_status(self):
        """Check if OAuth token exists"""
        token_file = Path("data/oauth_token_cache.json")

        if token_file.exists():
            self.oauth_status_label.setText("✓ Token guardado")
            self.oauth_status_label.setStyleSheet("color: green;")
        else:
            self.oauth_status_label.setText("Sin token")
            self.oauth_status_label.setStyleSheet("color: gray;")

    def update_oauth_status(self, authenticated: bool, email: str = ""):
        """Update OAuth status after authentication"""
        if authenticated:
            self.oauth_status_label.setText(f"✓ Autenticado: {email}")
            self.oauth_status_label.setStyleSheet("color: green;")
            if email:
                self.email_input.setText(email)
        else:
            self._check_oauth_status()

    def _on_save(self) -> None:
        """Handle save button click"""
        updated_config = {
            'github_repo_url': self.repo_url_input.text(),
            'check_updates_on_startup': self.check_updates_checkbox.isChecked(),
            'auto_update_enabled': self.auto_update_checkbox.isChecked(),
            'log_level': self.log_level_combo.currentText(),
            'output_directory': self.output_dir_input.text()
        }

        self.config_changed.emit(updated_config)

    def get_email_credentials(self) -> tuple:
        """Get email credentials"""
        return (self.email_input.text(), self.password_input.text())

    def set_email_credentials(self, email: str, password: str) -> None:
        """Set email credentials"""
        self.email_input.setText(email)
        self.password_input.setText(password)

    def _load_azure_config(self) -> None:
        """Load Azure configuration from file or environment variables"""
        config_file = Path("config/oauth_config.json")

        # Default values
        self.azure_client_id = ""
        self.azure_tenant_id = "common"

        # Try to load from JSON file first
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.azure_client_id = config.get('azure_client_id', '')
                    self.azure_tenant_id = config.get('azure_tenant_id', 'common')
                    self.logger.info("Loaded Azure config from oauth_config.json")
            except Exception as e:
                self.logger.warning(f"Error loading oauth_config.json: {e}")

        # Fallback to environment variables if not in file
        if not self.azure_client_id:
            self.azure_client_id = os.getenv('AZURE_CLIENT_ID', '')
            self.azure_tenant_id = os.getenv('AZURE_TENANT_ID', 'common')
            if self.azure_client_id:
                self.logger.info("Loaded Azure config from environment variables")

    def _on_save_azure_config(self) -> None:
        """Save Azure configuration to JSON file"""
        client_id = self.azure_client_id_input.text().strip()
        tenant_id = self.azure_tenant_id_input.text().strip()

        if not client_id:
            QMessageBox.warning(
                self,
                "Client ID Requerido",
                "Por favor ingresa el Client ID de Azure antes de guardar."
            )
            return

        if not tenant_id:
            tenant_id = "common"

        # Create config directory if it doesn't exist
        config_dir = Path("config")
        config_dir.mkdir(exist_ok=True)

        # Prepare config data
        config_data = {
            "azure_client_id": client_id,
            "azure_tenant_id": tenant_id,
            "enabled": True,
            "description": "Configuración OAuth 2.0 para Office 365",
            "last_updated": str(Path(__file__).stat().st_mtime)
        }

        # Save to file
        config_file = config_dir / "oauth_config.json"
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)

            # Update instance variables
            self.azure_client_id = client_id
            self.azure_tenant_id = tenant_id

            # Also update environment variables for current session
            os.environ['AZURE_CLIENT_ID'] = client_id
            os.environ['AZURE_TENANT_ID'] = tenant_id

            QMessageBox.information(
                self,
                "Guardado Exitoso",
                f"Las credenciales de Azure han sido guardadas en:\n{config_file}\n\n"
                "Las credenciales están disponibles inmediatamente."
            )

            self.logger.info(f"Azure config saved to {config_file}")

        except Exception as e:
            QMessageBox.critical(
                self,
                "Error al Guardar",
                f"No se pudo guardar la configuración:\n{e}"
            )
            self.logger.error(f"Error saving Azure config: {e}")
