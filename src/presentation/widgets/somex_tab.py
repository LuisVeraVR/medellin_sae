"""Somex Tab Widget - Presentation Layer"""
import logging
import tempfile
from pathlib import Path
from typing import Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLineEdit, QTableWidget, QTableWidgetItem, QMessageBox,
    QLabel, QHeaderView, QGroupBox, QFileDialog, QProgressDialog,
    QTextEdit, QInputDialog
)
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from src.infrastructure.sftp.somex_sftp_client import SomexSftpClient
from src.infrastructure.database.somex_repository import SomexRepository
from src.application.services.somex_processor_service import (
    SomexProcessorService,
    ItemsImporter
)


class ProcessingWorker(QThread):
    """Worker thread para procesamiento de ZIPs de Somex"""

    # Señales para comunicación con la UI
    progress_update = pyqtSignal(str)  # Mensaje de progreso
    processing_complete = pyqtSignal(dict)  # Resultados del procesamiento
    error_occurred = pyqtSignal(str)  # Mensaje de error

    def __init__(
        self,
        logger: logging.Logger,
        repository: SomexRepository,
        processor: SomexProcessorService,
        password: str
    ):
        super().__init__()
        self.logger = logger
        self.repository = repository
        self.processor = processor
        self.password = password
        self.sftp_client: Optional[SomexSftpClient] = None
        self.remote_dir = "/DocumentosPendientes"

    def run(self) -> None:
        """Ejecutar procesamiento automático de ZIPs"""
        try:
            # Conectar al SFTP
            self.progress_update.emit("Conectando a servidor SFTP de Somex...")
            self.sftp_client = SomexSftpClient(logger=self.logger)

            success, message = self.sftp_client.connect(
                self.remote_dir,
                password=self.password,
                max_retries=3,
                timeout=30
            )
            if not success:
                self.error_occurred.emit(f"Error de conexión: {message}")
                return

            self.progress_update.emit("Conexión exitosa. Listando archivos ZIP...")

            # Listar archivos ZIP
            all_files = self.sftp_client.list_files(self.remote_dir)
            zip_files = [
                f for f in all_files
                if not f['is_dir'] and f['name'].lower().endswith('.zip')
            ]

            if not zip_files:
                self.progress_update.emit(
                    "No se encontraron archivos ZIP en /DocumentosPendientes"
                )
                results = {
                    'total_zips': 0,
                    'processed_zips': 0,
                    'total_xmls': 0,
                    'processed_xmls': 0,
                    'skipped_xmls': 0,
                    'failed_xmls': 0
                }
                self.processing_complete.emit(results)
                return

            self.progress_update.emit(f"Encontrados {len(zip_files)} archivos ZIP")

            # Procesar cada ZIP
            total_results = {
                'total_zips': len(zip_files),
                'processed_zips': 0,
                'total_xmls': 0,
                'processed_xmls': 0,
                'skipped_xmls': 0,
                'failed_xmls': 0,
                'excel_file': None
            }

            # Acumular todas las facturas de todos los ZIPs
            all_invoices = []

            for idx, file_info in enumerate(zip_files, 1):
                zip_filename = file_info['name']
                self.progress_update.emit(
                    f"Procesando ZIP {idx}/{len(zip_files)}: {zip_filename}..."
                )

                try:
                    # Descargar ZIP a memoria
                    remote_path = f"{self.remote_dir}/{zip_filename}"

                    # Crear archivo temporal
                    with tempfile.NamedTemporaryFile(
                        delete=False,
                        suffix='.zip'
                    ) as tmp_file:
                        tmp_path = tmp_file.name

                    # Descargar archivo
                    success, message = self.sftp_client.download_file(
                        remote_path,
                        tmp_path
                    )

                    if not success:
                        self.logger.warning(
                            f"Error descargando {zip_filename}: {message}"
                        )
                        continue

                    # Procesar ZIP
                    results = self.processor.process_zip_file(tmp_path, zip_filename)

                    # Acumular resultados
                    total_results['processed_zips'] += 1
                    total_results['total_xmls'] += results['total_xmls']
                    total_results['processed_xmls'] += results['processed_xmls']
                    total_results['skipped_xmls'] += results['skipped_xmls']
                    total_results['failed_xmls'] += results['failed_xmls']

                    # Acumular facturas
                    all_invoices.extend(results['invoices'])

                    # Limpiar archivo temporal
                    Path(tmp_path).unlink(missing_ok=True)

                    self.progress_update.emit(
                        f"ZIP {zip_filename} procesado: "
                        f"{results['processed_xmls']} XMLs nuevos, "
                        f"{results['skipped_xmls']} ya procesados"
                    )

                except Exception as e:
                    self.logger.error(f"Error procesando {zip_filename}: {e}")
                    self.progress_update.emit(
                        f"Error en {zip_filename}: {str(e)}"
                    )

            # Generar Excel consolidado con todas las facturas
            self.logger.info(f"=== Before Excel generation ===")
            self.logger.info(f"Total invoices accumulated: {len(all_invoices)}")
            for idx, inv in enumerate(all_invoices, 1):
                self.logger.info(
                    f"  Invoice {idx}: {inv.get('invoice_number', 'N/A')} "
                    f"with {len(inv.get('items', []))} items"
                )

            if all_invoices:
                self.progress_update.emit(
                    f"\nGenerando Excel consolidado con {len(all_invoices)} facturas..."
                )

                try:
                    excel_path = self.processor.create_consolidated_excel(
                        all_invoices
                    )
                    total_results['excel_file'] = excel_path

                    # Marcar todos los XMLs como procesados
                    for invoice_data in all_invoices:
                        self.repository.mark_xml_processed(
                            invoice_data['xml_content'],
                            invoice_data['xml_filename'],
                            invoice_data['zip_filename'],
                            invoice_data.get('invoice_number'),
                            excel_path
                        )

                    self.progress_update.emit(
                        f"Excel consolidado creado: {excel_path}"
                    )

                    # Subir Excel a /DocumentosProcesados en SFTP
                    try:
                        excel_filename = Path(excel_path).name
                        remote_excel_path = f"/DocumentosProcesados/{excel_filename}"

                        self.progress_update.emit(
                            f"Subiendo Excel a SFTP: {excel_filename}..."
                        )

                        upload_success, upload_msg = self.sftp_client.upload_file(
                            excel_path,
                            remote_excel_path
                        )

                        if upload_success:
                            self.progress_update.emit(
                                f"✓ Excel subido a /DocumentosProcesados/{excel_filename}"
                            )
                        else:
                            self.logger.warning(
                                f"No se pudo subir Excel: {upload_msg}"
                            )
                            self.progress_update.emit(
                                f"⚠ No se pudo subir Excel al SFTP: {upload_msg}"
                            )
                    except Exception as e:
                        self.logger.error(f"Error subiendo Excel al SFTP: {e}")
                        self.progress_update.emit(
                            f"⚠ Error subiendo Excel: {str(e)}"
                        )

                except Exception as e:
                    self.logger.error(f"Error generando Excel consolidado: {e}")
                    self.progress_update.emit(
                        f"Error generando Excel: {str(e)}"
                    )

            self.processing_complete.emit(total_results)

        except Exception as e:
            self.logger.error(f"Error en procesamiento automático: {e}")
            self.error_occurred.emit(str(e))

        finally:
            if self.sftp_client:
                self.sftp_client.close()


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
        self.password = ""

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
        self.password = kwargs.get('password', '')

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

        # Intentar conectar con reintentos y timeout largo
        success, message = self.sftp_client.connect(
            self.remote_dir,
            password=self.password,
            max_retries=3,
            timeout=30
        )
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
        self.processing_worker: Optional[ProcessingWorker] = None
        self.current_files = []  # Lista de archivos actual

        # Initialize database and processor
        db_path = "data/somex_processing.db"
        self.repository = SomexRepository(db_path)
        self.processor = SomexProcessorService(
            repository=self.repository,
            logger=self.logger,
            output_dir="output/somex"
        )
        self.items_importer = ItemsImporter(
            logger=self.logger,
            repository=self.repository
        )

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
        self.remote_dir_input = QLineEdit("/DocumentosPendientes")
        self.remote_dir_input.setPlaceholderText("Ejemplo: /DocumentosPendientes")
        dir_layout.addWidget(self.remote_dir_input)
        config_layout.addLayout(dir_layout)

        # Info de servidor
        info_label = QLabel(
            "<i>Servidor: 170.239.154.159 (somexapp.com) | Puerto: 22 | "
            "Usuario: usuario.bolsaagro</i><br>"
            "<b>Nota:</b> La contraseña se solicitará en cada conexión y NO se guarda."
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

        # Grupo de Items
        items_group = QGroupBox("Importar Items")
        items_layout = QVBoxLayout()

        # Descripción de items
        items_desc = QLabel(
            "<b>Importar Excel con Items (CodigoItem, Referencia, Descripcion, etc.):</b><br>"
            "Este Excel se usa para hacer match con los productos de las facturas XML."
        )
        items_desc.setWordWrap(True)
        items_layout.addWidget(items_desc)

        # Botones de items
        items_btn_layout = QHBoxLayout()

        self.import_items_btn = QPushButton("Importar Excel de Items")
        self.import_items_btn.clicked.connect(self._on_import_items_clicked)
        items_btn_layout.addWidget(self.import_items_btn)

        self.view_items_btn = QPushButton("Ver Items Cargados")
        self.view_items_btn.clicked.connect(self._on_view_items_clicked)
        items_btn_layout.addWidget(self.view_items_btn)

        items_btn_layout.addStretch()
        items_layout.addLayout(items_btn_layout)

        # Label de estado de items
        self.items_status_label = QLabel("No se han importado items")
        self.items_status_label.setStyleSheet("color: gray; font-style: italic;")
        items_layout.addWidget(self.items_status_label)

        items_group.setLayout(items_layout)
        layout.addWidget(items_group)

        # Grupo de procesamiento automático
        auto_group = QGroupBox("Procesamiento Automático de ZIPs")
        auto_layout = QVBoxLayout()

        # Descripción
        desc_label = QLabel(
            "<b>Procesar automáticamente todos los ZIPs en /DocumentosPendientes:</b><br>"
            "- Descarga ZIPs desde el servidor SFTP<br>"
            "- Extrae XMLs de cada ZIP<br>"
            "- <b>Genera UN SOLO archivo Excel consolidado</b> con todas las facturas<br>"
            "- Evita reprocesar XMLs ya procesados"
        )
        desc_label.setWordWrap(True)
        auto_layout.addWidget(desc_label)

        # Botón de procesamiento
        self.process_btn = QPushButton("Procesar Todos los ZIPs")
        self.process_btn.clicked.connect(self._on_process_clicked)
        auto_layout.addWidget(self.process_btn)

        # Área de progreso
        progress_label = QLabel("Progreso:")
        auto_layout.addWidget(progress_label)

        self.progress_text = QTextEdit()
        self.progress_text.setReadOnly(True)
        self.progress_text.setMaximumHeight(150)
        auto_layout.addWidget(self.progress_text)

        # Estadísticas
        stats_layout = QHBoxLayout()
        stats_layout.addWidget(QLabel("Estadísticas:"))

        self.stats_btn = QPushButton("Ver Estadísticas")
        self.stats_btn.clicked.connect(self._on_stats_clicked)
        stats_layout.addWidget(self.stats_btn)

        stats_layout.addStretch()
        auto_layout.addLayout(stats_layout)

        auto_group.setLayout(auto_layout)
        layout.addWidget(auto_group)

        self.setLayout(layout)

    def _on_connect_clicked(self) -> None:
        """Manejar click en botón Conectar"""
        # Pedir contraseña al usuario
        password, ok = QInputDialog.getText(
            self,
            "Autenticación SFTP - Somex",
            "Ingrese la contraseña para usuario.bolsaagro:",
            QLineEdit.EchoMode.Password
        )

        if not ok or not password:
            QMessageBox.warning(
                self,
                "Contraseña Requerida",
                "Debe ingresar una contraseña para conectarse."
            )
            return

        # Deshabilitar botón durante la conexión
        self.connect_btn.setEnabled(False)
        self.status_input.setText("Conectando...")

        # Obtener directorio remoto
        remote_dir = self.remote_dir_input.text().strip() or "/"

        # Crear y configurar worker
        self.worker = SftpWorker(self.logger)
        self.worker.set_operation('connect', remote_dir=remote_dir, password=password)

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
                f"No se pudo conectar al servidor SFTP después de 3 intentos:\n\n{message}\n\n"
                "Posibles causas:\n"
                "- Contraseña incorrecta\n"
                "- Servidor no responde (timeout de red)\n"
                "- Problemas de conectividad\n"
                "- Firewall bloqueando el puerto 22\n\n"
                "El sistema intentó reconectar automáticamente con espera exponencial."
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

    def _on_process_clicked(self) -> None:
        """Manejar click en botón Procesar Todos los ZIPs"""
        # Pedir contraseña al usuario
        password, ok = QInputDialog.getText(
            self,
            "Autenticación SFTP - Somex",
            "Ingrese la contraseña para usuario.bolsaagro\n"
            "para conectarse y procesar los ZIPs:",
            QLineEdit.EchoMode.Password
        )

        if not ok or not password:
            QMessageBox.warning(
                self,
                "Contraseña Requerida",
                "Debe ingresar una contraseña para conectarse al servidor SFTP."
            )
            return

        # Confirmar con el usuario
        reply = QMessageBox.question(
            self,
            "Confirmar Procesamiento",
            "¿Desea procesar todos los archivos ZIP en /DocumentosPendientes?\n\n"
            "Esta operación:\n"
            "- Descargará todos los ZIPs del servidor\n"
            "- Extraerá los XMLs contenidos\n"
            "- Generará archivos Excel\n"
            "- Puede tomar varios minutos\n\n"
            "Los XMLs ya procesados serán omitidos automáticamente.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        # Limpiar área de progreso
        self.progress_text.clear()
        self.progress_text.append("Iniciando procesamiento automático...")

        # Deshabilitar botón durante procesamiento
        self.process_btn.setEnabled(False)

        # Crear y configurar worker de procesamiento
        self.processing_worker = ProcessingWorker(
            logger=self.logger,
            repository=self.repository,
            processor=self.processor,
            password=password
        )

        # Conectar señales
        self.processing_worker.progress_update.connect(self._on_progress_update)
        self.processing_worker.processing_complete.connect(
            self._on_processing_complete
        )
        self.processing_worker.error_occurred.connect(self._on_processing_error)

        # Iniciar worker
        self.processing_worker.start()

    def _on_progress_update(self, message: str) -> None:
        """Actualizar área de progreso"""
        self.progress_text.append(message)
        # Auto-scroll al final
        scrollbar = self.progress_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def _on_processing_complete(self, results: dict) -> None:
        """Manejar finalización del procesamiento"""
        self.process_btn.setEnabled(True)

        # Mostrar resumen
        summary = (
            f"\n{'='*60}\n"
            f"PROCESAMIENTO COMPLETADO\n"
            f"{'='*60}\n"
            f"ZIPs encontrados: {results['total_zips']}\n"
            f"ZIPs procesados: {results['processed_zips']}\n"
            f"XMLs totales: {results['total_xmls']}\n"
            f"XMLs procesados (nuevos): {results['processed_xmls']}\n"
            f"XMLs omitidos (ya procesados): {results['skipped_xmls']}\n"
            f"XMLs con errores: {results['failed_xmls']}\n"
        )

        if results.get('excel_file'):
            summary += f"\nArchivo Excel consolidado:\n{results['excel_file']}\n"
        else:
            summary += "\nNo se generó Excel (no hay facturas nuevas)\n"

        self.progress_text.append(summary)

        # Mostrar diálogo de confirmación
        if results.get('excel_file'):
            QMessageBox.information(
                self,
                "Procesamiento Completado",
                f"Procesamiento finalizado exitosamente.\n\n"
                f"XMLs procesados: {results['processed_xmls']}\n"
                f"Archivo Excel consolidado generado:\n"
                f"{results['excel_file']}\n\n"
                f"El archivo contiene todas las facturas procesadas."
            )
        else:
            QMessageBox.information(
                self,
                "Procesamiento Completado",
                f"Procesamiento finalizado.\n\n"
                f"XMLs procesados (nuevos): {results['processed_xmls']}\n"
                f"XMLs omitidos (ya procesados): {results['skipped_xmls']}\n\n"
                f"No se generó Excel porque no hay facturas nuevas."
            )

    def _on_processing_error(self, error_message: str) -> None:
        """Manejar errores durante el procesamiento"""
        self.process_btn.setEnabled(True)

        self.progress_text.append(f"\nERROR: {error_message}\n")

        QMessageBox.critical(
            self,
            "Error de Procesamiento",
            f"Ocurrió un error durante el procesamiento:\n\n{error_message}"
        )

    def _on_import_items_clicked(self) -> None:
        """Manejar click en botón Importar Items"""
        # Abrir diálogo para seleccionar Excel
        excel_path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar Excel de Items",
            "",
            "Excel Files (*.xlsx *.xls);;All Files (*.*)"
        )

        if not excel_path:
            return  # Usuario canceló

        try:
            # Importar items (se guardan automáticamente en BD)
            self.progress_text.append(f"Importando items desde: {excel_path}")

            items = self.items_importer.import_items_from_excel(excel_path)

            if not items:
                QMessageBox.warning(
                    self,
                    "Sin Items",
                    "No se encontraron items en el Excel.\n\n"
                    "Verifique que el archivo tenga las columnas correctas:\n"
                    "CodigoItem, Referencia, Descripcion, IdPlan, DescPlan, "
                    "IdMayor, DescripcionPlan, RowIdItem, Categoria"
                )
                return

            # Los items ya fueron guardados automáticamente en la BD
            count = len(items)

            # Actualizar status
            self.items_status_label.setText(
                f"✓ {count} items importados correctamente"
            )
            self.items_status_label.setStyleSheet("color: green;")

            self.progress_text.append(f"✓ {count} items importados exitosamente")

            QMessageBox.information(
                self,
                "Importación Exitosa",
                f"Se importaron {count} items correctamente.\n\n"
                f"Los items están listos para usar en el procesamiento de facturas."
            )

        except Exception as e:
            self.logger.error(f"Error importando items: {e}")
            self.progress_text.append(f"✗ Error importando items: {str(e)}")

            QMessageBox.critical(
                self,
                "Error de Importación",
                f"Error al importar items:\n\n{str(e)}\n\n"
                f"Verifique que el Excel tenga el formato correcto."
            )

    def _on_view_items_clicked(self) -> None:
        """Manejar click en botón Ver Items"""
        try:
            items = self.repository.get_all_items()

            if not items:
                QMessageBox.information(
                    self,
                    "Sin Items",
                    "No hay items importados.\n\n"
                    "Use el botón 'Importar Excel de Items' para cargar items."
                )
                return

            # Mostrar primeros 10 items
            items_text = f"Items Importados ({len(items)} total)\n"
            items_text += "=" * 60 + "\n\n"

            for i, item in enumerate(items[:10], 1):
                items_text += f"{i}. Código: {item['codigo_item']}\n"
                items_text += f"   Referencia: {item['referencia']}\n"
                items_text += f"   Descripción: {item['descripcion']}\n"
                items_text += f"   Categoría: {item['categoria']}\n\n"

            if len(items) > 10:
                items_text += f"\n... y {len(items) - 10} items más"

            QMessageBox.information(
                self,
                f"Items Cargados ({len(items)})",
                items_text
            )

        except Exception as e:
            self.logger.error(f"Error obteniendo items: {e}")
            QMessageBox.critical(
                self,
                "Error",
                f"Error al obtener items:\n\n{str(e)}"
            )

    def _on_stats_clicked(self) -> None:
        """Mostrar estadísticas de procesamiento"""
        try:
            stats = self.repository.get_processing_stats()

            stats_message = (
                f"Estadísticas de Procesamiento Somex\n"
                f"{'='*40}\n\n"
                f"XMLs procesados: {stats['xml_processed']}\n"
                f"Items guardados: {stats['items_count']}\n"
                f"Errores registrados: {stats['errors']}\n"
            )

            QMessageBox.information(
                self,
                "Estadísticas de Procesamiento",
                stats_message
            )

        except Exception as e:
            self.logger.error(f"Error obteniendo estadísticas: {e}")
            QMessageBox.critical(
                self,
                "Error",
                f"Error al obtener estadísticas:\n\n{str(e)}"
            )

    def closeEvent(self, event) -> None:
        """Manejar cierre del tab"""
        # Limpiar worker si existe
        if self.worker:
            self.worker.cleanup()
            self.worker.wait()

        # Limpiar processing worker si existe
        if self.processing_worker and self.processing_worker.isRunning():
            self.processing_worker.terminate()
            self.processing_worker.wait()

        event.accept()
