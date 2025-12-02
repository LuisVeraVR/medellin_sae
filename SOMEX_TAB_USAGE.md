# Tab Somex - Guía de Uso

## Descripción

El tab Somex permite conectarse a un servidor SFTP para listar, visualizar y descargar archivos XML y ZIP del cliente Somex.

## Configuración Inicial

### 1. Configurar Variable de Entorno

La contraseña SFTP **NO** está hardcodeada por seguridad. Debe configurarse como variable de entorno:

```bash
# En Linux/macOS
export SFTP_SOMEX_PASS="tu_contraseña_aqui"

# En Windows (CMD)
set SFTP_SOMEX_PASS=tu_contraseña_aqui

# En Windows (PowerShell)
$env:SFTP_SOMEX_PASS="tu_contraseña_aqui"
```

O agregar al archivo `.env` en la raíz del proyecto:

```
SFTP_SOMEX_PASS=tu_contraseña_aqui
```

### 2. Instalar Dependencias

Si es la primera vez, instalar `paramiko`:

```bash
pip install paramiko>=3.0.0
```

O instalar todas las dependencias:

```bash
pip install -r requirements.txt
```

## Características del Tab

### Información del Servidor

- **Host**: 170.239.154.159 (también soporta somexapp.com)
- **Puerto**: 22
- **Usuario**: usuario.bolsaagro
- **Contraseña**: Desde variable de entorno `SFTP_SOMEX_PASS`

### Funcionalidades

1. **Conectar al Servidor SFTP**
   - Ingresar el directorio remoto (por defecto `/`)
   - Clic en "Conectar y Listar XML"
   - El estado de la conexión se muestra en el campo de estado

2. **Listar Archivos XML/ZIP**
   - Automáticamente lista archivos después de conectar
   - Filtra solo archivos `.xml` y `.zip`
   - Muestra: nombre, tamaño (KB), fecha de modificación, tipo

3. **Descargar Archivos**
   - Seleccionar un archivo de la tabla
   - Clic en "Descargar Seleccionado"
   - Elegir ubicación local para guardar
   - Por defecto guarda en `downloads/somex/`

4. **Refrescar Lista**
   - Clic en "Refrescar Lista" para actualizar archivos disponibles

## Estructura de Código

### Capa de Infraestructura
`src/infrastructure/sftp/somex_sftp_client.py`

- **SomexSftpClient**: Clase para manejo de conexiones SFTP
  - `connect(remote_dir)`: Conectar al servidor
  - `list_files(remote_path)`: Listar todos los archivos
  - `list_xml_files(remote_path)`: Listar solo XML/ZIP
  - `download_file(remote_path, local_path)`: Descargar archivo
  - `close()`: Cerrar conexión de forma segura

### Capa de Presentación
`src/presentation/widgets/somex_tab.py`

- **SftpWorker**: Thread worker para operaciones en background (no bloquear UI)
- **SomexTab**: Widget del tab con interfaz gráfica
  - Botones de conexión y descarga
  - Tabla de archivos
  - Campo de estado
  - Manejo de errores con QMessageBox

### Integración
`src/presentation/main_window.py`

El tab se agrega automáticamente a la ventana principal en el método `_init_ui()`.

## Manejo de Errores

El sistema muestra errores en:
- Campo de estado (solo lectura)
- QMessageBox con detalles del error
- Logs de la aplicación

Errores comunes:
- **Variable de entorno no configurada**: `SFTP_SOMEX_PASS` no existe
- **Error de autenticación**: Usuario o contraseña incorrectos
- **Error de conexión**: Servidor no accesible o problemas de red
- **Error al listar archivos**: Directorio remoto no existe o sin permisos

## Buenas Prácticas Implementadas

1. **No bloquear UI**: Operaciones SFTP en QThread worker
2. **Manejo seguro de contraseñas**: Variable de entorno, no hardcoded
3. **Cierre correcto de conexiones**: Implementado en `closeEvent` y context manager
4. **Logging completo**: Todas las operaciones se registran
5. **Validación de errores**: Try-except en todas las operaciones críticas
6. **Separación de responsabilidades**: Infraestructura vs Presentación

## Ejemplo de Uso Programático

```python
from src.infrastructure.sftp.somex_sftp_client import SomexSftpClient
import logging

# Configurar logger
logger = logging.getLogger(__name__)

# Usar context manager para asegurar cierre
with SomexSftpClient(logger) as client:
    # Conectar
    success, msg = client.connect("/")

    if success:
        # Listar archivos XML
        xml_files = client.list_xml_files()

        for file in xml_files:
            print(f"{file['name']} - {file['size_kb']} KB")

        # Descargar archivo
        if xml_files:
            first_file = xml_files[0]['name']
            client.download_file(f"/{first_file}", f"./downloads/{first_file}")
```

## Próximas Mejoras Sugeridas

- [ ] Descarga múltiple de archivos
- [ ] Descargar todos los archivos de una vez
- [ ] Filtrado adicional (por fecha, tamaño, nombre)
- [ ] Vista previa de contenido XML
- [ ] Procesamiento automático después de descarga
- [ ] Programación de descargas automáticas
- [ ] Compresión/descompresión de archivos ZIP
