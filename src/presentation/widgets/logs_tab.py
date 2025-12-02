"""Logs Tab Widget - Presentation Layer"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit,
    QPushButton, QComboBox, QLabel
)


class LogsTab(QWidget):
    """Centralized logs tab widget"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self) -> None:
        """Initialize UI components"""
        layout = QVBoxLayout()

        # Filter controls
        filter_layout = QHBoxLayout()

        filter_layout.addWidget(QLabel("Nivel:"))

        self.level_filter = QComboBox()
        self.level_filter.addItems(['TODOS', 'DEBUG', 'INFO', 'WARNING', 'ERROR'])
        self.level_filter.currentTextChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(self.level_filter)

        filter_layout.addStretch()

        clear_btn = QPushButton("Limpiar Logs")
        clear_btn.clicked.connect(self._on_clear)
        filter_layout.addWidget(clear_btn)

        export_btn = QPushButton("Exportar Logs")
        export_btn.clicked.connect(self._on_export)
        filter_layout.addWidget(export_btn)

        layout.addLayout(filter_layout)

        # Log display
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        layout.addWidget(self.log_text)

        self.setLayout(layout)

    def add_log(self, level: str, message: str) -> None:
        """Add log message"""
        # Color code by level
        color = {
            'DEBUG': 'gray',
            'INFO': 'black',
            'WARNING': 'orange',
            'ERROR': 'red'
        }.get(level, 'black')

        html = f'<span style="color:{color};">[{level}] {message}</span>'
        self.log_text.append(html)

    def _on_filter_changed(self, level: str) -> None:
        """Handle filter change"""
        # TODO: Implement filtering logic
        pass

    def _on_clear(self) -> None:
        """Clear all logs"""
        self.log_text.clear()

    def _on_export(self) -> None:
        """Export logs to file"""
        from PyQt6.QtWidgets import QFileDialog
        from datetime import datetime

        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Exportar Logs",
            f"logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            "Text Files (*.txt)"
        )

        if filename:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(self.log_text.toPlainText())
