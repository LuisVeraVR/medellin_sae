"""Configuration Tab Widget - Presentation Layer"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLineEdit,
    QPushButton, QLabel, QGroupBox, QCheckBox, QComboBox
)
from PyQt6.QtCore import pyqtSignal


class ConfigTab(QWidget):
    """Configuration tab widget"""

    config_changed = pyqtSignal(dict)

    def __init__(self, config: dict, parent=None):
        super().__init__(parent)
        self.config = config
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

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("email@example.com")
        email_layout.addRow("Email:", self.email_input)

        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        email_layout.addRow("Password:", self.password_input)

        email_group.setLayout(email_layout)
        layout.addWidget(email_group)

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
