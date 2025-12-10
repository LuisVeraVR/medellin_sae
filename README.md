# Medellin SAE - Sistema de Procesamiento de Facturas Electrónicas

Aplicación de escritorio con PyQt6 para el procesamiento automático de facturas electrónicas UBL 2.1 desde correo electrónico, con auto-actualización desde GitHub y gestión de archivos SFTP.

## 🚀 Características

- ✅ **Arquitectura Clean**: Separación clara de capas (Domain, Application, Infrastructure, Presentation)
- ✅ **Multi-cliente**: Sistema de tabs para gestionar múltiples clientes
- ✅ **Tab Productos Pulgarin**: Base de datos de productos con importación desde Excel
- ✅ **Enriquecimiento CSV**: Agrega peso y U/M automáticamente a facturas de Pulgarin
- ✅ **Tab Somex SFTP**: Conexión SFTP para descarga de archivos XML/ZIP
- ✅ **Auto-actualización**: Actualización automática desde GitHub Releases
- ✅ **Procesamiento IMAP**: Conexión a Outlook/Office365 vía IMAP
- ✅ **Parser UBL 2.1**: Extracción de datos de XML en formato UBL 2.1 Colombia
- ✅ **Export CSV**: Exportación con formato personalizable (separadores, decimales)
- ✅ **SQLite Tracking**: Base de datos para evitar duplicados
- ✅ **Logging Completo**: Sistema de logs rotativo con niveles
- ✅ **GUI PyQt6**: Interfaz moderna con tabs y modo automático

## ⚡ Inicio Rápido

### 1. Requisitos Previos

- Python 3.9+ (Windows/Linux/macOS)
- Credenciales de email (Outlook/Office365)
- Para Somex: Contraseña SFTP

### 2. Instalación

```bash
# Clonar el repositorio
git clone https://github.com/LuisVeraVR/medellin_sae.git
cd medellin_sae

# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

### 3. Configurar Credenciales

Copiar `.env.example` a `.env`:

```bash
cp .env.example .env
```

Editar `.env` con tus credenciales:

```env
# Email Configuration
CORREAGRO_EMAIL=tu_email@outlook.com
CORREAGRO_PASSWORD=tu_password

# Somex SFTP Configuration
SFTP_SOMEX_PASS=tu_contraseña_sftp
```

### 4. Ejecutar

```bash
python run.py
```

## 📱 Tabs Disponibles

### Tab Productos Pulgarin - Base de Datos de Productos

El tab de Productos Pulgarin permite gestionar una base de datos de productos para enriquecer automáticamente las facturas procesadas.

#### Características

- **Importación Excel**: Importa productos desde archivos Excel (.xlsx, .xls)
- **Validación automática**: Verifica que las columnas requeridas existan
- **Normalización**: Hace matching inteligente ignorando mayúsculas y espacios extra
- **Actualización**: Actualiza productos existentes o crea nuevos
- **Visualización**: Tabla con todos los productos importados
- **Búsqueda**: Busca productos por código o descripción

#### Formato del Archivo Excel

El archivo Excel debe contener las siguientes columnas (no importa mayúsculas/minúsculas):

- **Codigo**: Código del producto (puede estar vacío)
- **Descripcion**: Nombre/descripción del producto (requerido)
- **PESO**: Peso del producto (requerido)
- **U/M**: Unidad de medida (requerido)

#### Enriquecimiento Automático

Cuando se procesan facturas de Pulgarin, el sistema automáticamente:

1. Busca cada producto por código o descripción
2. Normaliza textos para mejor matching ("ARROZ  Blanco" coincide con "arroz blanco")
3. Agrega columnas **Peso** y **U/M BD** al CSV generado
4. Deja vacío si el producto no está en la base de datos

Esto permite tener datos adicionales de productos directamente en el CSV de salida.

### Tab Somex - Gestión SFTP

El tab Somex permite conectarse al servidor SFTP para descargar archivos XML/ZIP del cliente Somex.

#### Configuración Somex

**Información del servidor:**
- Host: `170.239.154.159` (también `somexapp.com`)
- Puerto: `22`
- Usuario: `usuario.bolsaagro`
- Contraseña: Variable de entorno `SFTP_SOMEX_PASS`

#### Uso del Tab Somex

1. **Conectar**: Ingresar directorio remoto (por defecto `/`) y clic en "Conectar y Listar XML"
2. **Listar**: Automáticamente muestra archivos XML y ZIP con: nombre, tamaño (KB), fecha, tipo
3. **Descargar**: Seleccionar archivo y clic en "Descargar Seleccionado"
4. **Refrescar**: Actualizar lista con el botón "Refrescar Lista"

#### Errores Comunes Somex

- **Variable no configurada**: Asegurar que `SFTP_SOMEX_PASS` esté en `.env`
- **Error de autenticación**: Verificar usuario y contraseña
- **Error de conexión**: Verificar acceso al servidor y red

### Tabs de Clientes

Cada cliente habilitado tiene su propio tab con:
- Botón "Procesar Ahora" para procesamiento manual
- Modo automático configurable por intervalo
- Estadísticas de procesamiento
- Log de operaciones

## 📁 Estructura del Proyecto

```
medellin_sae/
├── src/
│   ├── domain/              # Capa de dominio
│   │   ├── entities/        # Entidades de negocio
│   │   ├── repositories/    # Interfaces abstractas
│   │   └── use_cases/       # Casos de uso
│   ├── application/         # Capa de aplicación
│   │   ├── services/        # Servicios
│   │   └── dto/            # Data Transfer Objects
│   ├── infrastructure/      # Implementaciones concretas
│   │   ├── email/          # Repositorio IMAP
│   │   ├── xml/            # Parser UBL 2.1
│   │   ├── sftp/           # Cliente SFTP (Somex)
│   │   ├── database/       # SQLite
│   │   ├── github/         # Auto-update
│   │   └── csv/            # Export CSV
│   └── presentation/        # GUI PyQt6
│       ├── widgets/        # Tabs y widgets
│       │   ├── client_tab.py
│       │   ├── somex_tab.py
│       │   ├── pulgarin_products_tab.py  # NEW: Tab de productos
│       │   ├── config_tab.py
│       │   └── logs_tab.py
│       └── main_window.py
├── config/
│   ├── clients.json        # Configuración de clientes
│   └── app_config.json     # Configuración general
├── data/                   # Bases de datos SQLite
│   └── app.db             # BD de productos Pulgarin
├── logs/                   # Logs de la aplicación
├── output/                 # CSVs generados
├── installer_output/       # Instaladores generados
├── requirements.txt
├── version.txt
├── build.py               # Script de build con PyInstaller
├── create_installer.py    # Script para crear instalador
├── installer.iss          # Script de Inno Setup
├── run.py
├── BUILD.md               # Guía de construcción
└── README.md
```

## ⚙️ Configuración

### Agregar Nuevo Cliente

Editar `config/clients.json`:

```json
{
  "clients": [
    {
      "id": "nuevo_cliente",
      "name": "Nombre del Cliente",
      "enabled": true,
      "email_config": {
        "search_criteria": "(UNSEEN SUBJECT \"PALABRA CLAVE\")",
        "imap_server": "outlook.office365.com"
      },
      "xml_config": {
        "format": "ubl_2.1"
      },
      "output_config": {
        "csv_delimiter": ";",
        "decimal_separator": ",",
        "decimal_places": 5
      }
    }
  ]
}
```

### Configuración de la Aplicación

Editar `config/app_config.json`:

```json
{
  "github_repo_url": "https://github.com/LuisVeraVR/medellin_sae",
  "check_updates_on_startup": true,
  "auto_update_enabled": true,
  "log_level": "INFO",
  "output_directory": "output"
}
```

### Modo Automático

1. Activar "Modo Automático" en el tab del cliente
2. Configurar intervalo en minutos
3. La aplicación procesará automáticamente

## 📊 Formato CSV de Salida

El CSV generado incluye 22 campos base (separador `;`, encoding UTF-8-BOM):

- N° Factura
- Nombre Producto
- Codigo Subyacente
- Unidad Medida en Kg,Un,Lt
- Cantidad (5 decimales, separador coma)
- Precio Unitario (5 decimales, separador coma)
- Fecha Factura (YYYY-MM-DD)
- Fecha Pago (YYYY-MM-DD)
- Nit Comprador / Nombre Comprador
- Nit Vendedor / Nombre Vendedor
- Principal V,C
- Municipio
- Iva
- Descripción
- Activa / Factura Activa
- Bodega
- Incentivo
- Cantidad Original
- Moneda

### Columnas Adicionales para Pulgarin

Cuando se procesan facturas de **Pulgarin**, se agregan 2 columnas adicionales:

- **Peso**: Peso del producto desde la base de datos
- **U/M BD**: Unidad de medida desde la base de datos

Estas columnas se llenan automáticamente buscando el producto en la base de datos. Si el producto no se encuentra, las columnas quedan vacías.

## 🔨 Build Ejecutable e Instalador

### Crear Ejecutable

Para crear un ejecutable independiente (Windows):

```bash
python build.py
```

El ejecutable se generará en `dist/MedellinSAE.exe`

### Crear Instalador Profesional

Para crear un instalador de Windows con Inno Setup:

1. Instala [Inno Setup 6](https://jrsoftware.org/isdl.php)
2. Ejecuta:

```bash
python build.py
python create_installer.py
```

El instalador se generará en `installer_output/MedellinSAE_Setup_v1.0.0.exe`

### Documentación Completa

Para instrucciones detalladas sobre cómo crear el ejecutable, instalador y distribuir la aplicación, consulta:

**📘 [BUILD.md](BUILD.md)** - Guía completa de construcción e instalación

El instalador incluye:
- ✅ Instalación guiada en español/inglés
- ✅ Accesos directos en menú de inicio y escritorio
- ✅ Creación automática de directorios
- ✅ Desinstalador completo
- ✅ Detección de versiones

## 🔄 Auto-actualización

La aplicación verifica automáticamente al inicio si hay actualizaciones disponibles en GitHub Releases.

### Crear un Release

1. Incrementar versión en `version.txt`:
   ```
   v1.2.0
   ```

2. Hacer commit y push:
   ```bash
   git commit -am "Release v1.2.0"
   git push
   ```

3. Crear tag:
   ```bash
   git tag v1.2.0
   git push --tags
   ```

4. Crear release en GitHub con el ejecutable adjunto

La aplicación detectará automáticamente la nueva versión.

## 🐛 Troubleshooting

### Error de Conexión IMAP

- ✅ Verificar credenciales en `.env`
- ✅ Habilitar autenticación de aplicaciones en Outlook
- ✅ Verificar servidor IMAP: `outlook.office365.com`
- ✅ Revisar logs en `logs/app.log`

### Error al Parsear XML

- ✅ Verificar formato UBL 2.1
- ✅ Revisar namespaces en `src/infrastructure/xml/ubl_xml_parser.py`
- ✅ Verificar que el ZIP contenga XML

### Error SFTP Somex

- ✅ Verificar `SFTP_SOMEX_PASS` en `.env`
- ✅ Comprobar conexión al servidor `170.239.154.159`
- ✅ Verificar usuario: `usuario.bolsaagro`

### No se Detectan Actualizaciones

- ✅ Verificar `github_repo_url` en `config/app_config.json`
- ✅ Verificar releases públicos en GitHub
- ✅ Revisar logs en `logs/app.log`

## 📝 Logs

Los logs se guardan en:
- `logs/app.log` - Log general de la aplicación
- `logs/{client_id}_{date}.log` - Logs por cliente

Niveles de log (configurables en `config/app_config.json`):
- **DEBUG**: Información detallada
- **INFO**: Información general
- **WARNING**: Advertencias
- **ERROR**: Errores

## 🏗️ Arquitectura

### Clean Architecture

El proyecto sigue los principios de Clean Architecture con 4 capas:

1. **Domain Layer**: Entidades de negocio e interfaces (independiente de frameworks)
2. **Application Layer**: Casos de uso y servicios de aplicación
3. **Infrastructure Layer**: Implementaciones técnicas (IMAP, SFTP, SQLite, etc.)
4. **Presentation Layer**: GUI PyQt6 con tabs y widgets

### Flujo de Procesamiento

```
Email IMAP → Extract ZIP → Parse XML UBL → Validate → Save to SQLite → Export CSV
```

### Flujo SFTP Somex

```
Connect SFTP → List XML/ZIP files → Download → Process (opcional)
```

## 🔧 Tecnologías Utilizadas

- **PyQt6**: GUI moderna y responsiva
- **paramiko**: Cliente SFTP para Somex
- **lxml**: Parsing XML UBL 2.1
- **imaplib**: Conexión IMAP a email
- **sqlite3**: Base de datos para tracking
- **python-dotenv**: Gestión de variables de entorno
- **requests**: HTTP para auto-actualización

## 💡 Consejos de Uso

1. **Primer Procesamiento**: Puede tomar tiempo si hay muchos correos sin procesar
2. **Modo Automático**: Ideal para monitoreo continuo
3. **Backup CSV**: Los archivos incluyen timestamp, no se sobreescriben
4. **SQLite Deduplication**: Evita procesar el mismo correo dos veces
5. **Logs Detallados**: Revisar logs para debugging y auditoría
6. **Somex SFTP**: Descargar archivos antes de procesar manualmente
7. **Variables de Entorno**: Nunca hacer commit del archivo `.env`

## 🤝 Contribuir

1. Fork el proyecto
2. Crear rama feature: `git checkout -b feature/nueva-funcionalidad`
3. Commit cambios: `git commit -am 'feat: Agregar nueva funcionalidad'`
4. Push a la rama: `git push origin feature/nueva-funcionalidad`
5. Crear Pull Request

## 📄 Licencia

Este proyecto es privado y propietario.

## 👤 Autor

**Luis Vera**
- GitHub: [@LuisVeraVR](https://github.com/LuisVeraVR)

## 🆘 Soporte

Para reportar bugs o solicitar features:
https://github.com/LuisVeraVR/medellin_sae/issues

## 📚 Referencias Técnicas

### UBL 2.1 Namespaces

```python
NAMESPACES = {
    'cac': 'urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2',
    'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2',
}
```

### Criterios de Búsqueda IMAP

```python
# Emails no leídos con asunto específico
"(UNSEEN SUBJECT \"COMERCIALIZADORA TRIPLE A\")"

# Emails de remitente específico
"(FROM \"sender@example.com\")"

# Emails recientes
"(SINCE \"01-Jan-2024\")"
```

### Ejemplo Uso Programático SFTP

```python
from src.infrastructure.sftp.somex_sftp_client import SomexSftpClient
import logging

logger = logging.getLogger(__name__)

# Context manager asegura cierre de conexión
with SomexSftpClient(logger) as client:
    success, msg = client.connect("/")

    if success:
        # Listar archivos XML
        xml_files = client.list_xml_files()

        for file in xml_files:
            print(f"{file['name']} - {file['size_kb']} KB")

        # Descargar primer archivo
        if xml_files:
            first_file = xml_files[0]['name']
            client.download_file(f"/{first_file}", f"./downloads/{first_file}")
```

## ✅ Checklist Pre-Producción

- [ ] Credenciales configuradas en `.env`
- [ ] Conexión IMAP funcionando
- [ ] Procesamiento manual exitoso
- [ ] CSV generado correctamente
- [ ] Somex SFTP conecta y lista archivos
- [ ] Logs sin errores críticos
- [ ] Modo automático configurado (si aplica)
- [ ] Backup de código y datos
- [ ] Ejecutable compilado (si aplica)

---

**Versión**: 1.0.0
**Última actualización**: Diciembre 2024
