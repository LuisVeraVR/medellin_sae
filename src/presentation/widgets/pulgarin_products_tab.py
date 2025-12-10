"""Pulgarin Products Tab Widget - Presentation Layer"""
import logging
from pathlib import Path
from typing import Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QLabel, QGroupBox,
    QFileDialog, QMessageBox, QHeaderView, QProgressDialog
)
from PyQt6.QtCore import Qt
from src.infrastructure.database.sqlite_repository import SQLiteRepository
import pandas as pd


class PulgarinProductsTab(QWidget):
    """Tab widget for Pulgarin products management"""

    def __init__(self, logger: logging.Logger, parent=None):
        super().__init__(parent)
        self.logger = logger

        # Initialize database repository
        db_path = Path("data") / "app.db"
        self.db_repo = SQLiteRepository(str(db_path))

        self._init_ui()
        self._load_products()

    def _init_ui(self) -> None:
        """Initialize UI components"""
        layout = QVBoxLayout()

        # Header
        header_label = QLabel("<h2>Base de Datos de Productos Pulgarin</h2>")
        layout.addWidget(header_label)

        # Control buttons
        controls_layout = QHBoxLayout()

        self.import_btn = QPushButton("📂 Importar Excel")
        self.import_btn.setToolTip("Importar productos desde archivo Excel (Codigo, Descripcion, PESO, U/M)")
        self.import_btn.clicked.connect(self._on_import_excel)
        controls_layout.addWidget(self.import_btn)

        self.refresh_btn = QPushButton("🔄 Actualizar")
        self.refresh_btn.clicked.connect(self._load_products)
        controls_layout.addWidget(self.refresh_btn)

        self.clear_btn = QPushButton("🗑️ Limpiar Base de Datos")
        self.clear_btn.setStyleSheet("background-color: #dc3545; color: white;")
        self.clear_btn.clicked.connect(self._on_clear_database)
        controls_layout.addWidget(self.clear_btn)

        controls_layout.addStretch()
        layout.addLayout(controls_layout)

        # Statistics
        stats_group = QGroupBox("Estadísticas")
        stats_layout = QHBoxLayout()

        self.count_label = QLabel("Total de productos: 0")
        stats_layout.addWidget(self.count_label)

        stats_layout.addStretch()
        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)

        # Products table
        table_group = QGroupBox("Productos")
        table_layout = QVBoxLayout()

        self.products_table = QTableWidget()
        self.products_table.setColumnCount(6)
        self.products_table.setHorizontalHeaderLabels([
            "ID", "Código", "Descripción", "Peso", "U/M", "Última Actualización"
        ])

        # Configure table
        self.products_table.setAlternatingRowColors(True)
        self.products_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.products_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        # Auto-resize columns
        header = self.products_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # ID
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Codigo
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)  # Descripcion
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Peso
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # U/M
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)  # Updated At

        table_layout.addWidget(self.products_table)
        table_group.setLayout(table_layout)
        layout.addWidget(table_group)

        # Info label
        info_label = QLabel(
            "<i>Formato Excel esperado: Codigo, Descripcion, PESO, U/M (todos como texto, Codigo puede estar vacío)</i>"
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        self.setLayout(layout)

    def _on_import_excel(self) -> None:
        """Handle import Excel button click"""
        # Open file dialog
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar archivo Excel",
            "",
            "Excel Files (*.xlsx *.xls);;All Files (*)"
        )

        if not file_path:
            return

        try:
            # Show progress dialog
            progress = QProgressDialog("Importando productos...", "Cancelar", 0, 100, self)
            progress.setWindowModality(Qt.WindowModality.WindowModal)
            progress.setValue(0)

            self.logger.info(f"Importing products from: {file_path}")

            # Read Excel file
            df = pd.read_excel(file_path)
            progress.setValue(10)

            # Validate columns
            required_columns = ['Codigo', 'Descripcion', 'PESO', 'U/M']

            # Check if columns exist (case-insensitive)
            df.columns = df.columns.str.strip()
            column_mapping = {}
            for req_col in required_columns:
                found = False
                for col in df.columns:
                    if col.lower() == req_col.lower():
                        column_mapping[col] = req_col
                        found = True
                        break
                if not found and req_col != 'Codigo':  # Codigo puede faltar
                    raise ValueError(f"Columna requerida no encontrada: {req_col}")

            # Rename columns to standard names
            df = df.rename(columns=column_mapping)
            progress.setValue(20)

            # Add missing columns if needed
            for col in required_columns:
                if col not in df.columns:
                    df[col] = None

            # Process and save products
            total_rows = len(df)
            imported_count = 0
            updated_count = 0
            error_count = 0

            for index, row in df.iterrows():
                if progress.wasCanceled():
                    break

                try:
                    # Extract data
                    codigo = str(row['Codigo']).strip() if pd.notna(row['Codigo']) and str(row['Codigo']).strip() != '' else None
                    descripcion = str(row['Descripcion']).strip() if pd.notna(row['Descripcion']) else ''
                    peso = str(row['PESO']).strip() if pd.notna(row['PESO']) else ''
                    um = str(row['U/M']).strip() if pd.notna(row['U/M']) else ''

                    # Validate required fields
                    if not descripcion or not peso or not um:
                        self.logger.warning(f"Skipping row {index + 1}: Missing required fields")
                        error_count += 1
                        continue

                    # Check if product exists
                    existing = None
                    if codigo:
                        existing = self.db_repo.get_product_by_code(codigo)

                    # Save product
                    self.db_repo.save_product(
                        codigo=codigo,
                        descripcion=descripcion,
                        peso=peso,
                        um=um
                    )

                    if existing:
                        updated_count += 1
                    else:
                        imported_count += 1

                except Exception as e:
                    self.logger.error(f"Error processing row {index + 1}: {str(e)}")
                    error_count += 1

                # Update progress
                progress.setValue(20 + int((index + 1) / total_rows * 70))

            progress.setValue(100)

            # Show results
            result_msg = f"Importación completada:\n\n"
            result_msg += f"✓ Productos nuevos: {imported_count}\n"
            result_msg += f"↻ Productos actualizados: {updated_count}\n"
            if error_count > 0:
                result_msg += f"✗ Errores: {error_count}\n"

            QMessageBox.information(self, "Importación Completada", result_msg)

            self.logger.info(f"Import completed: {imported_count} new, {updated_count} updated, {error_count} errors")

            # Reload products table
            self._load_products()

        except Exception as e:
            error_msg = f"Error al importar archivo Excel:\n{str(e)}"
            self.logger.error(error_msg)
            QMessageBox.critical(self, "Error de Importación", error_msg)

    def _load_products(self) -> None:
        """Load products from database and display in table"""
        try:
            # Get all products
            products = self.db_repo.get_all_products()

            # Update count
            count = len(products)
            self.count_label.setText(f"Total de productos: {count}")

            # Clear table
            self.products_table.setRowCount(0)

            # Populate table
            for product in products:
                row_position = self.products_table.rowCount()
                self.products_table.insertRow(row_position)

                # ID
                self.products_table.setItem(row_position, 0,
                    QTableWidgetItem(str(product['id'])))

                # Codigo (puede ser NULL)
                codigo_text = product['codigo'] if product['codigo'] else ""
                self.products_table.setItem(row_position, 1,
                    QTableWidgetItem(codigo_text))

                # Descripcion
                self.products_table.setItem(row_position, 2,
                    QTableWidgetItem(product['descripcion']))

                # Peso
                self.products_table.setItem(row_position, 3,
                    QTableWidgetItem(product['peso']))

                # U/M
                self.products_table.setItem(row_position, 4,
                    QTableWidgetItem(product['um']))

                # Updated At
                self.products_table.setItem(row_position, 5,
                    QTableWidgetItem(str(product['updated_at'])))

            self.logger.info(f"Loaded {count} products from database")

        except Exception as e:
            error_msg = f"Error al cargar productos: {str(e)}"
            self.logger.error(error_msg)
            QMessageBox.critical(self, "Error", error_msg)

    def _on_clear_database(self) -> None:
        """Handle clear database button click"""
        reply = QMessageBox.question(
            self,
            "Confirmar Limpieza",
            "¿Está seguro de que desea eliminar TODOS los productos de la base de datos?\n\n"
            "Esta acción no se puede deshacer.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                # Get all products and delete them
                products = self.db_repo.get_all_products()
                deleted_count = 0

                for product in products:
                    if self.db_repo.delete_product(product_id=product['id']):
                        deleted_count += 1

                QMessageBox.information(
                    self,
                    "Limpieza Completada",
                    f"Se eliminaron {deleted_count} productos de la base de datos."
                )

                self.logger.info(f"Cleared {deleted_count} products from database")

                # Reload table
                self._load_products()

            except Exception as e:
                error_msg = f"Error al limpiar base de datos: {str(e)}"
                self.logger.error(error_msg)
                QMessageBox.critical(self, "Error", error_msg)
