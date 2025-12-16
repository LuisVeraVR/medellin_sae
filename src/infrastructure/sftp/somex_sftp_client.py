"""Somex SFTP Client - Infrastructure Layer"""
import os
import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import paramiko
from pathlib import Path
import time


class SomexSftpClient:
    """Cliente SFTP para conectar y gestionar archivos del servidor Somex"""

    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Inicializar cliente SFTP

        Args:
            logger: Logger opcional para registro de eventos
        """
        self.logger = logger or logging.getLogger(__name__)
        self.ssh_client: Optional[paramiko.SSHClient] = None
        self.sftp_client: Optional[paramiko.SFTPClient] = None
        self.connected = False

        # Configuración de conexión
        self.host = "170.239.154.159"  # También puede ser "somexapp.com"
        self.port = 22
        self.username = "usuario.bolsaagro"

    def connect(
        self,
        remote_dir: str = "/",
        password: Optional[str] = None,
        max_retries: int = 3,
        timeout: int = 30
    ) -> Tuple[bool, str]:
        """
        Establecer conexión SFTP con el servidor con reintentos automáticos

        Args:
            remote_dir: Directorio remoto al que navegar después de conectar
            password: Contraseña para autenticación (si es None, intenta leer de variable de entorno)
            max_retries: Número máximo de intentos de conexión (por defecto 3)
            timeout: Timeout de conexión en segundos (por defecto 30)

        Returns:
            Tupla (éxito, mensaje de estado)
        """
        # Validar contraseña
        pwd = password or os.getenv('SFTP_SOMEX_PASS', '')
        if not pwd:
            return False, "Error: Se requiere contraseña. Proporcione el parámetro 'password' o configure SFTP_SOMEX_PASS"

        # Intentar conectar con reintentos
        last_error = None
        for attempt in range(1, max_retries + 1):
            try:
                self.logger.info(
                    f"Intento {attempt}/{max_retries}: Conectando a {self.host}:{self.port} "
                    f"como {self.username}..."
                )

                # Crear cliente SSH
                self.ssh_client = paramiko.SSHClient()

                # Configurar política de claves (aceptar claves desconocidas)
                self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

                # Configurar timeouts más agresivos para manejar conexiones lentas
                self.logger.info(f"Timeout configurado: {timeout} segundos")

                # Conectar al servidor
                self.ssh_client.connect(
                    hostname=self.host,
                    port=self.port,
                    username=self.username,
                    password=pwd,
                    timeout=timeout,
                    banner_timeout=timeout,
                    auth_timeout=timeout
                )

                # Abrir sesión SFTP
                self.sftp_client = self.ssh_client.open_sftp()

                # Cambiar al directorio remoto
                try:
                    self.sftp_client.chdir(remote_dir)
                    current_dir = self.sftp_client.getcwd()
                    self.logger.info(f"Directorio actual: {current_dir}")
                except IOError as e:
                    self.logger.warning(f"No se pudo cambiar a {remote_dir}: {e}")
                    # Continuar de todos modos

                self.connected = True
                self.logger.info(f"✓ Conexión exitosa en el intento {attempt}")
                return True, f"Conectado exitosamente a {self.host}"

            except paramiko.AuthenticationException as e:
                error_msg = "Error de autenticación: Usuario o contraseña incorrectos"
                self.logger.error(error_msg)
                # No reintentar en caso de error de autenticación
                return False, error_msg

            except (paramiko.SSHException, OSError, Exception) as e:
                last_error = e
                error_type = type(e).__name__
                error_msg = str(e)

                self.logger.warning(
                    f"✗ Intento {attempt}/{max_retries} falló: {error_type}: {error_msg}"
                )

                # Si no es el último intento, esperar antes de reintentar
                if attempt < max_retries:
                    wait_time = 2 ** attempt  # Backoff exponencial: 2, 4, 8 segundos
                    self.logger.info(f"Esperando {wait_time} segundos antes del siguiente intento...")
                    time.sleep(wait_time)

                    # Limpiar cliente SSH anterior
                    if self.ssh_client:
                        try:
                            self.ssh_client.close()
                        except:
                            pass
                        self.ssh_client = None
                        self.sftp_client = None

        # Si llegamos aquí, todos los intentos fallaron
        final_error = f"Error de conexión después de {max_retries} intentos: {str(last_error)}"
        self.logger.error(final_error)
        return False, final_error

    def list_files(self, remote_path: str = ".") -> List[Dict[str, any]]:
        """
        Listar todos los archivos en un directorio remoto

        Args:
            remote_path: Ruta del directorio remoto (por defecto el actual)

        Returns:
            Lista de diccionarios con información de archivos
        """
        if not self.connected or not self.sftp_client:
            raise ConnectionError("No hay conexión SFTP activa")

        try:
            files_info = []

            # Obtener lista de archivos
            file_attrs = self.sftp_client.listdir_attr(remote_path)

            for attr in file_attrs:
                # Obtener información del archivo
                file_info = {
                    'name': attr.filename,
                    'size': attr.st_size,  # Tamaño en bytes
                    'size_kb': round(attr.st_size / 1024, 2),  # Tamaño en KB
                    'modified': datetime.fromtimestamp(attr.st_mtime),
                    'is_dir': self._is_directory(attr)
                }
                files_info.append(file_info)

            self.logger.info(f"Listados {len(files_info)} archivos/directorios")
            return files_info

        except IOError as e:
            self.logger.error(f"Error al listar archivos: {e}")
            raise

    def list_xml_files(self, remote_path: str = ".") -> List[Dict[str, any]]:
        """
        Listar solo archivos XML y ZIP en un directorio remoto

        Args:
            remote_path: Ruta del directorio remoto

        Returns:
            Lista de diccionarios con información de archivos XML/ZIP
        """
        all_files = self.list_files(remote_path)

        # Filtrar solo archivos XML y ZIP
        xml_files = [
            f for f in all_files
            if not f['is_dir'] and (
                f['name'].lower().endswith('.xml') or
                f['name'].lower().endswith('.zip')
            )
        ]

        self.logger.info(f"Encontrados {len(xml_files)} archivos XML/ZIP")
        return xml_files

    def download_file(self, remote_path: str, local_path: str) -> Tuple[bool, str]:
        """
        Descargar un archivo del servidor SFTP

        Args:
            remote_path: Ruta del archivo remoto
            local_path: Ruta donde guardar el archivo localmente

        Returns:
            Tupla (éxito, mensaje)
        """
        if not self.connected or not self.sftp_client:
            return False, "No hay conexión SFTP activa"

        try:
            # Crear directorio local si no existe
            local_dir = Path(local_path).parent
            local_dir.mkdir(parents=True, exist_ok=True)

            # Descargar archivo
            self.sftp_client.get(remote_path, local_path)

            success_msg = f"Archivo descargado: {remote_path} -> {local_path}"
            self.logger.info(success_msg)
            return True, success_msg

        except IOError as e:
            error_msg = f"Error al descargar archivo: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"Error inesperado: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg

    def download_items_catalog(self, local_path: str = "data/ListadoItems.xlsx") -> Tuple[bool, str]:
        """
        Descargar el catálogo de items desde /Items/ListadoItems

        Args:
            local_path: Ruta local donde guardar el archivo (por defecto data/ListadoItems.xlsx)

        Returns:
            Tupla (éxito, mensaje)
        """
        if not self.connected or not self.sftp_client:
            return False, "No hay conexión SFTP activa"

        try:
            # Buscar archivo en /Items que contenga "ListadoItems"
            items_dir = "/Items"
            self.logger.info(f"Buscando archivo de items en {items_dir}")

            try:
                files = self.sftp_client.listdir(items_dir)
                self.logger.info(f"Archivos en {items_dir}: {files}")

                # Buscar archivo que contenga "ListadoItems"
                items_file = None
                for file in files:
                    if "ListadoItems" in file or "listadoitems" in file.lower():
                        items_file = file
                        break

                if not items_file:
                    return False, f"No se encontró archivo de items en {items_dir}"

                remote_path = f"{items_dir}/{items_file}"
                self.logger.info(f"Descargando {remote_path}...")

                # Descargar archivo
                return self.download_file(remote_path, local_path)

            except IOError as e:
                error_msg = f"Error al acceder a {items_dir}: {str(e)}"
                self.logger.error(error_msg)
                return False, error_msg

        except Exception as e:
            error_msg = f"Error descargando catálogo de items: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg

    def upload_file(self, local_path: str, remote_path: str) -> Tuple[bool, str]:
        """
        Subir un archivo al servidor SFTP

        Args:
            local_path: Ruta del archivo local
            remote_path: Ruta donde guardar el archivo remotamente

        Returns:
            Tupla (éxito, mensaje)
        """
        if not self.connected or not self.sftp_client:
            return False, "No hay conexión SFTP activa"

        try:
            # Verificar que el archivo local existe
            if not Path(local_path).exists():
                return False, f"El archivo local no existe: {local_path}"

            # Crear directorio remoto si no existe
            remote_dir = os.path.dirname(remote_path)
            if remote_dir and remote_dir != '/':
                try:
                    self.sftp_client.stat(remote_dir)
                except IOError:
                    # El directorio no existe, intentar crearlo
                    try:
                        self.sftp_client.mkdir(remote_dir)
                        self.logger.info(f"Directorio remoto creado: {remote_dir}")
                    except IOError as e:
                        self.logger.warning(
                            f"No se pudo crear directorio {remote_dir}: {e}. "
                            f"Intentando subir de todos modos..."
                        )

            # Subir archivo
            self.sftp_client.put(local_path, remote_path)

            success_msg = f"Archivo subido: {local_path} -> {remote_path}"
            self.logger.info(success_msg)
            return True, success_msg

        except IOError as e:
            error_msg = f"Error al subir archivo: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"Error inesperado al subir: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg

    def move_to_processed(
        self,
        remote_filename: str,
        source_dir: str = "/DocumentosPendientes",
        dest_dir: str = "/DocumentosProcesados"
    ) -> Tuple[bool, str]:
        """
        Mover un archivo de la carpeta de pendientes a procesados

        Args:
            remote_filename: Nombre del archivo a mover
            source_dir: Directorio origen (por defecto /DocumentosPendientes)
            dest_dir: Directorio destino (por defecto /DocumentosProcesados)

        Returns:
            Tupla (éxito, mensaje)
        """
        if not self.connected or not self.sftp_client:
            return False, "No hay conexión SFTP activa"

        try:
            source_path = f"{source_dir}/{remote_filename}"
            dest_path = f"{dest_dir}/{remote_filename}"

            # Verificar que el archivo origen existe
            try:
                self.sftp_client.stat(source_path)
            except IOError:
                return False, f"El archivo origen no existe: {source_path}"

            # Crear directorio destino si no existe
            try:
                self.sftp_client.stat(dest_dir)
            except IOError:
                try:
                    self.sftp_client.mkdir(dest_dir)
                    self.logger.info(f"Directorio creado: {dest_dir}")
                except IOError as e:
                    return False, f"No se pudo crear directorio {dest_dir}: {str(e)}"

            # Mover archivo (renombrar)
            self.sftp_client.rename(source_path, dest_path)

            success_msg = f"Archivo movido: {source_path} -> {dest_path}"
            self.logger.info(success_msg)
            return True, success_msg

        except IOError as e:
            error_msg = f"Error al mover archivo: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"Error inesperado al mover archivo: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg

    def get_file_info(self, remote_path: str) -> Optional[Dict[str, any]]:
        """
        Obtener información de un archivo específico

        Args:
            remote_path: Ruta del archivo remoto

        Returns:
            Diccionario con información del archivo o None si no existe
        """
        if not self.connected or not self.sftp_client:
            raise ConnectionError("No hay conexión SFTP activa")

        try:
            attr = self.sftp_client.stat(remote_path)

            return {
                'name': os.path.basename(remote_path),
                'size': attr.st_size,
                'size_kb': round(attr.st_size / 1024, 2),
                'modified': datetime.fromtimestamp(attr.st_mtime),
                'is_dir': self._is_directory(attr)
            }
        except IOError:
            return None

    def close(self) -> None:
        """Cerrar la conexión SFTP de manera segura"""
        try:
            if self.sftp_client:
                self.sftp_client.close()
                self.logger.info("Cliente SFTP cerrado")

            if self.ssh_client:
                self.ssh_client.close()
                self.logger.info("Cliente SSH cerrado")

            self.connected = False

        except Exception as e:
            self.logger.error(f"Error al cerrar conexión: {e}")

    def _is_directory(self, attr: paramiko.SFTPAttributes) -> bool:
        """
        Verificar si un atributo corresponde a un directorio

        Args:
            attr: Atributos del archivo SFTP

        Returns:
            True si es directorio, False en caso contrario
        """
        import stat
        return stat.S_ISDIR(attr.st_mode)

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - asegurar cierre de conexión"""
        self.close()
