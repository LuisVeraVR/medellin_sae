# Medellin SAE - Sistema de Procesamiento de Facturas Electrónicas

Aplicación de escritorio con PyQt6 para el procesamiento automático de facturas electrónicas UBL 2.1 desde correo electrónico, con auto-actualización desde GitHub.

## 🚀 Características

- ✅ **Arquitectura Clean**: Separación clara de capas (Domain, Application, Infrastructure, Presentation)
- ✅ **Multi-cliente**: Sistema de tabs para gestionar múltiples clientes
- ✅ **Auto-actualización**: Actualización automática desde GitHub Releases
- ✅ **Procesamiento IMAP**: Conexión a Outlook/Office365 vía IMAP
- ✅ **Parser UBL 2.1**: Extracción de datos de XML en formato UBL 2.1 Colombia
- ✅ **Export CSV**: Exportación con formato personalizable (separadores, decimales)
- ✅ **SQLite Tracking**: Base de datos para evitar duplicados
- ✅ **Logging Completo**: Sistema de logs rotativo con niveles
- ✅ **GUI PyQt6**: Interfaz moderna con tabs y modo automático

## 📋 Requisitos

- Python 3.9+
- Windows/Linux/macOS
- Credenciales de email (Outlook/Office365)

## 🔧 Instalación

### 1. Clonar el repositorio

```bash
git clone https://github.com/LuisVeraVR/medellin_sae.git
cd medellin_sae
```

### 2. Crear entorno virtual

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/macOS
source venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar credenciales

Copiar `.env.example` a `.env` y configurar:

```bash
cp .env.example .env
```

Editar `.env`:

```env
CORREAGRO_EMAIL=tu_email@example.com
CORREAGRO_PASSWORD=tu_password
```

## 🎯 Uso

### Ejecutar en modo desarrollo

```bash
python run.py
```

### Build ejecutable (Windows)

```bash
python build.py
```

El ejecutable se generará en `dist/MedellinSAE.exe`

## 📁 Estructura del Proyecto

```
medellin_sae/
├── src/
│   ├── domain/              # Capa de dominio (entidades, casos de uso)
│   │   ├── entities/
│   │   ├── repositories/    # Interfaces abstractas
│   │   └── use_cases/
│   ├── application/         # Capa de aplicación (servicios, DTOs)
│   │   ├── services/
│   │   └── dto/
│   ├── infrastructure/      # Implementaciones concretas
│   │   ├── email/          # IMAP
│   │   ├── xml/            # Parser UBL 2.1
│   │   ├── database/       # SQLite
│   │   ├── github/         # Auto-update
│   │   └── csv/            # Export CSV
│   └── presentation/        # GUI PyQt6
│       ├── widgets/
│       └── main_window.py
├── config/
│   ├── clients.json        # Configuración de clientes
│   └── app_config.json     # Configuración general
├── data/                   # Bases de datos SQLite
├── logs/                   # Logs de la aplicación
├── output/                 # CSVs generados
├── requirements.txt
├── version.txt
├── build.py
├── run.py
└── README.md
```

## ⚙️ Configuración

### Agregar nuevo cliente

Editar `config/clients.json`:

```json
{
  "clients": [
    {
      "id": "nuevo_cliente",
      "name": "Nombre del Cliente",
      "enabled": true,
      "email_config": {
        "search_criteria": "(UNSEEN SUBJECT \"CRITERIO DE BÚSQUEDA\")",
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

### Configuración de la aplicación

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

## 📊 Formato CSV de Salida

El CSV generado incluye los siguientes campos (separador `;`, encoding UTF-8-BOM):

- N° Factura
- Nombre Producto
- Codigo Subyacente
- Unidad Medida en Kg,Un,Lt
- Cantidad (5 decimales, separador coma)
- Precio Unitario (5 decimales, separador coma)
- Fecha Factura (YYYY-MM-DD)
- Fecha Pago (YYYY-MM-DD)
- Nit Comprador
- Nombre Comprador
- Nit Vendedor
- Nombre Vendedor
- Principal V,C
- Municipio
- Iva
- Descripción
- Activa
- Factura Activa
- Bodega
- Incentivo
- Cantidad Original
- Moneda

## 🔄 Auto-actualización

La aplicación verifica automáticamente al inicio si hay actualizaciones disponibles en GitHub Releases.

### Crear un release

1. Incrementar versión en `version.txt`:
   ```
   v1.1.0
   ```

2. Hacer commit y push:
   ```bash
   git commit -am "Release v1.1.0"
   git push
   ```

3. Crear tag:
   ```bash
   git tag v1.1.0
   git push --tags
   ```

4. Crear release en GitHub con el ejecutable

La aplicación detectará automáticamente la nueva versión y ofrecerá actualizar.

## 🐛 Troubleshooting

### Error de conexión IMAP

- Verificar credenciales en `.env`
- Asegurar que la autenticación de aplicaciones esté habilitada en Outlook
- Verificar que el servidor IMAP sea correcto (`outlook.office365.com`)

### Error al parsear XML

- Verificar que el XML sea formato UBL 2.1
- Revisar los namespaces en `src/infrastructure/xml/ubl_xml_parser.py`

### No se detectan actualizaciones

- Verificar `github_repo_url` en `config/app_config.json`
- Verificar que el repositorio tenga releases públicos
- Revisar los logs en `logs/app.log`

## 📝 Logs

Los logs se guardan en:
- `logs/app.log` - Log general de la aplicación
- `logs/{client_id}_{date}.log` - Logs por cliente

Niveles de log:
- DEBUG: Información detallada
- INFO: Información general
- WARNING: Advertencias
- ERROR: Errores

## 🏗️ Arquitectura

### Clean Architecture

El proyecto sigue los principios de Clean Architecture:

1. **Domain Layer**: Entidades de negocio e interfaces
2. **Application Layer**: Casos de uso y servicios
3. **Infrastructure Layer**: Implementaciones técnicas
4. **Presentation Layer**: GUI PyQt6

### Flujo de procesamiento

```
Email IMAP → Extract ZIP → Parse XML UBL → Save to SQLite → Export CSV
```

## 🤝 Contribuir

1. Fork el proyecto
2. Crear rama feature (`git checkout -b feature/nueva-caracteristica`)
3. Commit cambios (`git commit -am 'Agregar nueva característica'`)
4. Push a la rama (`git push origin feature/nueva-caracteristica`)
5. Crear Pull Request

## 📄 Licencia

Este proyecto es privado y propietario.

## 👤 Autor

**Luis Vera**
- GitHub: [@LuisVeraVR](https://github.com/LuisVeraVR)

## 🆘 Soporte

Para reportar bugs o solicitar features, crear un issue en:
https://github.com/LuisVeraVR/medellin_sae/issues

## 📚 Documentación Adicional

### UBL 2.1 Namespaces

```python
NAMESPACES = {
    'cac': 'urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2',
    'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2',
}
```

### Criterios de búsqueda IMAP

Ejemplos de criterios de búsqueda:

```python
# Emails no leídos con asunto específico
"(UNSEEN SUBJECT \"COMERCIALIZADORA TRIPLE A\")"

# Emails de un remitente específico
"(FROM \"sender@example.com\")"

# Emails de los últimos 7 días
"(SINCE \"01-Jan-2024\")"
```

---

**Versión**: 1.0.0
**Última actualización**: 2024
