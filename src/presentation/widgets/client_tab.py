"""Client Tab Widget - Presentation Layer"""
import os
import logging
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTextEdit, QLabel, QCheckBox, QSpinBox, QGroupBox
)
from PyQt6.QtCore import QTimer, pyqtSignal
from src.domain.entities.client import Client
from src.domain.entities.processing_result import ProcessingResult


class ClientTab(QWidget):
    """Tab widget for individual client"""

    processing_requested = pyqtSignal(str)  # Signal with client_id

    def __init__(self, client: Client, logger: logging.Logger, parent=None):
        super().__init__(parent)
        self.client = client
        self.logger = logger
        self.auto_timer = QTimer()
        self.auto_timer.timeout.connect(self._on_auto_process)

        self._init_ui()

    def _init_ui(self) -> None:
        """Initialize UI components"""
        layout = QVBoxLayout()

        # Client info
        info_label = QLabel(f"<h2>{self.client.name}</h2>")
        layout.addWidget(info_label)

        # Control buttons
        controls_layout = QHBoxLayout()

        self.process_btn = QPushButton("Procesar Ahora")
        self.process_btn.clicked.connect(self._on_process_now)
        controls_layout.addWidget(self.process_btn)

        self.open_output_btn = QPushButton("Abrir Carpeta Output")
        self.open_output_btn.clicked.connect(self._on_open_output)
        controls_layout.addWidget(self.open_output_btn)

        controls_layout.addStretch()
        layout.addLayout(controls_layout)

        # Auto-process controls
        auto_group = QGroupBox("Procesamiento Automático")
        auto_layout = QHBoxLayout()

        self.auto_checkbox = QCheckBox("Modo Automático")
        self.auto_checkbox.stateChanged.connect(self._on_auto_mode_changed)
        auto_layout.addWidget(self.auto_checkbox)

        auto_layout.addWidget(QLabel("Intervalo (minutos):"))

        self.interval_spin = QSpinBox()
        self.interval_spin.setMinimum(1)
        self.interval_spin.setMaximum(1440)  # Max 24 hours
        self.interval_spin.setValue(15)
        auto_layout.addWidget(self.interval_spin)

        auto_layout.addStretch()
        auto_group.setLayout(auto_layout)
        layout.addWidget(auto_group)

        # Statistics
        stats_group = QGroupBox("Estadísticas")
        stats_layout = QHBoxLayout()

        self.emails_label = QLabel("Correos procesados: 0")
        stats_layout.addWidget(self.emails_label)

        self.invoices_label = QLabel("Facturas generadas: 0")
        stats_layout.addWidget(self.invoices_label)

        self.errors_label = QLabel("Errores: 0")
        stats_layout.addWidget(self.errors_label)

        stats_layout.addStretch()
        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)

        # Log display
        log_group = QGroupBox("Log de Procesamiento")
        log_layout = QVBoxLayout()

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(200)
        log_layout.addWidget(self.log_text)

        clear_log_btn = QPushButton("Limpiar Log")
        clear_log_btn.clicked.connect(self.log_text.clear)
        log_layout.addWidget(clear_log_btn)

        log_group.setLayout(log_layout)
        layout.addWidget(log_group)

        self.setLayout(layout)

    def _on_process_now(self) -> None:
        """Handle process now button click"""
        self.log_message("Iniciando procesamiento manual...")
        self.process_btn.setEnabled(False)
        self.processing_requested.emit(self.client.id)

    def _on_auto_mode_changed(self, state: int) -> None:
        """Handle auto mode checkbox change"""
        if state:
            interval_minutes = self.interval_spin.value()
            interval_ms = interval_minutes * 60 * 1000
            self.auto_timer.start(interval_ms)
            self.log_message(f"Modo automático activado (cada {interval_minutes} minutos)")
        else:
            self.auto_timer.stop()
            self.log_message("Modo automático desactivado")

    def _on_auto_process(self) -> None:
        """Handle automatic processing trigger"""
        self.log_message("Procesamiento automático iniciado...")
        self.processing_requested.emit(self.client.id)

    def _on_open_output(self) -> None:
        """Open output folder in file explorer"""
        output_path = Path("output") / self.client.id
        output_path.mkdir(parents=True, exist_ok=True)

        # Open folder in system file explorer
        if os.name == 'nt':  # Windows
            os.startfile(output_path)
        elif os.name == 'posix':  # macOS and Linux
            os.system(f'xdg-open "{output_path}"')

    def log_message(self, message: str) -> None:
        """Add message to log display"""
        self.log_text.append(message)
        self.logger.info(f"[{self.client.id}] {message}")

    def update_stats(self, result: ProcessingResult) -> None:
        """Update statistics display"""
        self.emails_label.setText(f"Correos procesados: {result.emails_processed}")
        self.invoices_label.setText(f"Facturas generadas: {result.invoices_generated}")
        self.errors_label.setText(f"Errores: {result.errors_count}")

        if result.success:
            self.log_message(f"✓ Procesamiento completado: {result.invoices_generated} facturas")
            if result.output_file:
                self.log_message(f"  Archivo: {result.output_file}")
        else:
            self.log_message(f"✗ Procesamiento con errores")
            for error in result.error_messages:
                self.log_message(f"  Error: {error}")

        self.process_btn.setEnabled(True)

    def processing_finished(self) -> None:
        """Re-enable process button after processing"""
        self.process_btn.setEnabled(True)
