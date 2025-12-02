"""Somex Tab Widget - Presentation Layer"""
import logging
from pathlib import Path
from typing import Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLineEdit, QTableWidget, QTableWidgetItem, QMessageBox,
    QLabel, QHeaderView, QGroupBox, QFileDialog
)
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from src.infrastructure.sftp.somex_sftp_client import SomexSftpClient


class SftpWorker(QThread):
    """Worker thread para operaciones SFTP (evitar bloquear la UI)"""

    # Señales para comunicación con la UI
    connection_result = pyqtSignal(bool, str)  # (success, message)
    files_listed = pyqtSignal(list)  # Lista de archivos
    download_result = pyqtSignal(bool, str)  # (success, message)
    error_occurred = pyqtSignal(str)  # Mensaje de error

    def __init__(self, logger: logging.Logger):
        super().__init__()
        self.logger = logger
        self.sftp_client: Optional[SomexSftpClient] = None
        self.operation = None  # 'connect', 'list', 'download'
        self.remote_dir = "/"
        self.remote_file = ""
        self.local_file = ""

    def set_operation(self, operation: str, **kwargs) -> None:
        """
        Configurar operación a ejecutar

        Args:
            operation: Tipo de operación ('connect', 'list', 'download')
            **kwargs: Parámetros adicionales según la operación
        """
        self.operation = operation
        self.remote_dir = kwargs.get('remote_dir', '/')
        self.remote_file = kwargs.get('remote_file', '')
        self.local_file = kwargs.get('local_file', '')

    def run(self) -> None:
        """Ejecutar operación SFTP en background"""
        try:
            if self.operation == 'connect':
                self._connect_and_list()
            elif self.operation == 'download':
                self._download_file()
        except Exception as e:
            self.logger.error(f"Error en worker SFTP: {str(e)}")
            self.error_occurred.emit(str(e))

    def _connect_and_list(self) -> None:
        """Conectar al servidor y listar archivos XML"""
        # Crear nuevo cliente SFTP
        self.sftp_client = SomexSftpClient(logger=self.logger)

        # Intentar conectar
        success, message = self.sftp_client.connect(self.remote_dir)
        self.connection_result.emit(success, message)

        if success:
            try:
                # Listar archivos XML
                xml_files = self.sftp_client.list_xml_files(self.remote_dir)
                self.files_listed.emit(xml_files)
            except Exception as e:
                error_msg = f"Error al listar archivos: {str(e)}"
                self.logger.error(error_msg)
                self.error_occurred.emit(error_msg)

    def _download_file(self) -> None:
        """Descargar un archivo específico"""
        if not self.sftp_client or not self.sftp_client.connected:
            self.error_occurred.emit("No hay conexión SFTP activa")
            return

        success, message = self.sftp_client.download_file(
            self.remote_file,
            self.local_file
        )
        self.download_result.emit(success, message)

    def cleanup(self) -> None:
        """Limpiar recursos al finalizar"""
        if self.sftp_client:
            self.sftp_client.close()


class SomexTab(QWidget):
    """Tab para gestión de archivos XML del cliente Somex vía SFTP"""

    def __init__(self, logger: logging.Logger, parent=None):
        super().__init__(parent)
        self.logger = logger
        self.worker: Optional[SftpWorker] = None
        self.current_files = []  # Lista de archivos actual

        self._init_ui()

    def _init_ui(self) -> None:
        """Inicializar componentes de la interfaz"""
        layout = QVBoxLayout()

        # Título
        title_label = QLabel("<h2>Somex - Descarga de XML vía SFTP</h2>")
        layout.addWidget(title_label)

        # Grupo de configuración
        config_group = QGroupBox("Configuración")
        config_layout = QVBoxLayout()

        # Directorio remoto
        dir_layout = QHBoxLayout()
        dir_layout.addWidget(QLabel("Directorio remoto:"))
        self.remote_dir_input = QLineEdit("/")
        self.remote_dir_input.setPlaceholderText("Ejemplo: / o /entrada")
        dir_layout.addWidget(self.remote_dir_input)
        config_layout.addLayout(dir_layout)

        # Info de servidor
        info_label = QLabel(
            "<i>Servidor: 170.239.154.159 (somexapp.com) | Puerto: 22 | "
            "Usuario: usuario.bolsaagro</i>"
        )
        info_label.setWordWrap(True)
        config_layout.addWidget(info_label)

        config_group.setLayout(config_layout)
        layout.addWidget(config_group)

        # Grupo de conexión
        connection_group = QGroupBox("Conexión")
        connection_layout = QVBoxLayout()

        # Botón de conectar
        self.connect_btn = QPushButton("Conectar y Listar XML")
        self.connect_btn.clicked.connect(self._on_connect_clicked)
        connection_layout.addWidget(self.connect_btn)

        # Estado de conexión
        status_layout = QHBoxLayout()
        status_layout.addWidget(QLabel("Estado:"))
        self.status_input = QLineEdit()
        self.status_input.setReadOnly(True)
        self.status_input.setPlaceholderText("No conectado")
        status_layout.addWidget(self.status_input)
        connection_layout.addLayout(status_layout)

        connection_group.setLayout(connection_layout)
        layout.addWidget(connection_group)

        # Grupo de archivos
        files_group = QGroupBox("Archivos XML/ZIP Disponibles")
        files_layout = QVBoxLayout()

        # Tabla de archivos
        self.files_table = QTableWidget()
        self.files_table.setColumnCount(4)
        self.files_table.setHorizontalHeaderLabels([
            "Nombre", "Tamaño (KB)", "Fecha Modificación", "Tipo"
        ])

        # Configurar tabla
        self.files_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.files_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        header = self.files_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)

        files_layout.addWidget(self.files_table)

        # Botones de acción
        actions_layout = QHBoxLayout()

        self.download_btn = QPushButton("Descargar Seleccionado")
        self.download_btn.clicked.connect(self._on_download_clicked)
        self.download_btn.setEnabled(False)
        actions_layout.addWidget(self.download_btn)

        self.refresh_btn = QPushButton("Refrescar Lista")
        self.refresh_btn.clicked.connect(self._on_refresh_clicked)
        self.refresh_btn.setEnabled(False)
        actions_layout.addWidget(self.refresh_btn)

        actions_layout.addStretch()
        files_layout.addLayout(actions_layout)

        files_group.setLayout(files_layout)
        layout.addWidget(files_group)

        self.setLayout(layout)

    def _on_connect_clicked(self) -> None:
        """Manejar click en botón Conectar"""
        # Deshabilitar botón durante la conexión
        self.connect_btn.setEnabled(False)
        self.status_input.setText("Conectando...")

        # Obtener directorio remoto
        remote_dir = self.remote_dir_input.text().strip() or "/"

        # Crear y configurar worker
        self.worker = SftpWorker(self.logger)
        self.worker.set_operation('connect', remote_dir=remote_dir)

        # Conectar señales
        self.worker.connection_result.connect(self._on_connection_result)
        self.worker.files_listed.connect(self._on_files_listed)
        self.worker.error_occurred.connect(self._on_error)
        self.worker.finished.connect(self._on_worker_finished)

        # Iniciar worker
        self.worker.start()

    def _on_connection_result(self, success: bool, message: str) -> None:
        """Manejar resultado de conexión"""
        self.status_input.setText(message)

        if not success:
            # Mostrar error en cuadro de diálogo
            QMessageBox.critical(
                self,
                "Error de Conexión",
                f"No se pudo conectar al servidor SFTP:\n\n{message}\n\n"
                "Verifique:\n"
                "- Variable de entorno SFTP_SOMEX_PASS está configurada\n"
                "- Credenciales son correctas\n"
                "- Servidor es accesible"
            )
            self.connect_btn.setEnabled(True)

    def _on_files_listed(self, files: list) -> None:
        """Manejar lista de archivos recibida"""
        self.current_files = files

        # Limpiar tabla
        self.files_table.setRowCount(0)

        # Llenar tabla con archivos
        for file_info in files:
            row = self.files_table.rowCount()
            self.files_table.insertRow(row)

            # Nombre
            name_item = QTableWidgetItem(file_info['name'])
            self.files_table.setItem(row, 0, name_item)

            # Tamaño en KB
            size_item = QTableWidgetItem(str(file_info['size_kb']))
            size_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.files_table.setItem(row, 1, size_item)

            # Fecha de modificación
            date_str = file_info['modified'].strftime('%Y-%m-%d %H:%M:%S')
            date_item = QTableWidgetItem(date_str)
            self.files_table.setItem(row, 2, date_item)

            # Tipo de archivo
            file_type = "ZIP" if file_info['name'].lower().endswith('.zip') else "XML"
            type_item = QTableWidgetItem(file_type)
            type_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.files_table.setItem(row, 3, type_item)

        # Habilitar botones
        self.download_btn.setEnabled(len(files) > 0)
        self.refresh_btn.setEnabled(True)
        self.connect_btn.setEnabled(True)

        # Actualizar estado
        self.status_input.setText(f"Conectado - {len(files)} archivos encontrados")

    def _on_download_clicked(self) -> None:
        """Manejar click en botón Descargar"""
        # Obtener fila seleccionada
        selected_rows = self.files_table.selectionModel().selectedRows()

        if not selected_rows:
            QMessageBox.warning(
                self,
                "Selección Requerida",
                "Por favor, seleccione un archivo para descargar"
            )
            return

        row = selected_rows[0].row()
        file_info = self.current_files[row]
        filename = file_info['name']

        # Obtener directorio remoto
        remote_dir = self.remote_dir_input.text().strip() or "/"
        remote_path = f"{remote_dir}/{filename}" if remote_dir != "/" else f"/{filename}"

        # Seleccionar ubicación de descarga
        default_path = str(Path("downloads") / "somex" / filename)
        local_path, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar Archivo",
            default_path,
            "XML Files (*.xml);;ZIP Files (*.zip);;All Files (*.*)"
        )

        if not local_path:
            return  # Usuario canceló

        # Deshabilitar botones durante descarga
        self.download_btn.setEnabled(False)
        self.status_input.setText(f"Descargando {filename}...")

        # Configurar worker para descarga
        if self.worker and self.worker.sftp_client:
            self.worker.set_operation(
                'download',
                remote_file=remote_path,
                local_file=local_path
            )
            self.worker.download_result.connect(self._on_download_result)
            self.worker.start()

    def _on_download_result(self, success: bool, message: str) -> None:
        """Manejar resultado de descarga"""
        if success:
            QMessageBox.information(
                self,
                "Descarga Exitosa",
                message
            )
            self.status_input.setText("Descarga completada")
        else:
            QMessageBox.critical(
                self,
                "Error de Descarga",
                f"No se pudo descargar el archivo:\n\n{message}"
            )
            self.status_input.setText("Error en descarga")

        self.download_btn.setEnabled(True)

    def _on_refresh_clicked(self) -> None:
        """Refrescar lista de archivos"""
        self._on_connect_clicked()

    def _on_error(self, error_message: str) -> None:
        """Manejar errores generales"""
        self.logger.error(f"Error SFTP: {error_message}")
        self.status_input.setText(f"Error: {error_message}")
        QMessageBox.critical(
            self,
            "Error",
            f"Ocurrió un error:\n\n{error_message}"
        )
        self.connect_btn.setEnabled(True)

    def _on_worker_finished(self) -> None:
        """Limpiar cuando el worker termina"""
        # No cerrar la conexión aquí para permitir múltiples descargas
        pass

    def closeEvent(self, event) -> None:
        """Manejar cierre del tab"""
        # Limpiar worker si existe
        if self.worker:
            self.worker.cleanup()
            self.worker.wait()

        event.accept()
