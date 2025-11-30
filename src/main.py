"""Main Entry Point - Medellin SAE"""
import sys
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from src.presentation.main_window import MainWindow


def main():
    """Main application entry point"""
    # Enable High DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("Medellin SAE")
    app.setOrganizationName("MedellinSAE")

    # Create and show main window
    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
