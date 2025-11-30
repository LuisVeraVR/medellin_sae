# Guía de Inicio Rápido - Medellin SAE

Esta guía te ayudará a poner en marcha la aplicación en menos de 5 minutos.

## ⚡ Inicio Rápido

### 1. Requisitos Previos

- Python 3.9 o superior instalado
- Git instalado
- Credenciales de correo Outlook/Office365

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

### 3. Configuración de Credenciales

Crear archivo `.env` en la raíz del proyecto:

```env
CORREAGRO_EMAIL=tu_email@outlook.com
CORREAGRO_PASSWORD=tu_password
```

### 4. Ejecutar la Aplicación

```bash
python run.py
```

## 🎯 Primer Uso

1. **Configurar Email**: Ve a la pestaña "Configuración" e ingresa tus credenciales
2. **Verificar Cliente**: Revisa la configuración del cliente "Comercializadora Triple A"
3. **Procesar**: Haz clic en "Procesar Ahora" en la pestaña del cliente
4. **Revisar Output**: Los CSV se generan en `output/triple_a/`

## ⚙️ Configuración Avanzada

### Agregar Nuevo Cliente

Editar `config/clients.json` y agregar:

```json
{
  "id": "cliente_nuevo",
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
```

Reiniciar la aplicación para ver el nuevo tab.

### Modo Automático

1. En el tab del cliente, activar "Modo Automático"
2. Configurar intervalo en minutos
3. La aplicación procesará automáticamente según el intervalo

### Minimizar a Bandeja

La aplicación se puede minimizar a la bandeja del sistema. Hacer doble clic en el icono para restaurar.

## 🔨 Build Ejecutable

Para crear un ejecutable independiente:

```bash
python build.py
```

El ejecutable estará en `dist/MedellinSAE.exe`

## 📊 Estructura de Datos

### Formato de Email Esperado

- **Asunto**: Debe contener "COMERCIALIZADORA TRIPLE A" (configurable)
- **Adjuntos**: Archivo ZIP
- **Contenido ZIP**: PDF + XML (UBL 2.1)

### Formato CSV Generado

22 columnas separadas por `;`, encoding UTF-8-BOM:
- Información de factura (número, fechas)
- Datos de producto (nombre, código, cantidad, precio)
- Información de comprador/vendedor (NIT, nombre)
- Detalles adicionales (municipio, IVA, etc.)

## 🐛 Solución de Problemas

### Error: "No se puede conectar al servidor IMAP"

**Solución**: 
- Verificar credenciales en `.env`
- Habilitar "Autenticación de aplicaciones" en Outlook
- Verificar conexión a internet

### Error: "No se encuentra el archivo XML"

**Solución**:
- Verificar que el ZIP contenga un archivo XML
- Revisar que sea formato UBL 2.1
- Verificar logs en `logs/app.log`

### Error: "No se pueden instalar las dependencias"

**Solución**:
```bash
# Actualizar pip
python -m pip install --upgrade pip

# Instalar de nuevo
pip install -r requirements.txt
```

## 📝 Logs y Debug

Los logs se encuentran en:
- `logs/app.log` - Log general
- `logs/triple_a_YYYYMMDD.log` - Log por cliente

Nivel de log se configura en `config/app_config.json`:
```json
{
  "log_level": "DEBUG"  // DEBUG, INFO, WARNING, ERROR
}
```

## 🔄 Actualizaciones

La aplicación verifica automáticamente actualizaciones al iniciar.

Para actualizar manualmente:
1. Hacer pull del repositorio
2. Instalar nuevas dependencias: `pip install -r requirements.txt`
3. Reiniciar aplicación

## 💡 Consejos

1. **Primer Procesamiento**: Puede tomar tiempo si hay muchos correos
2. **Modo Automático**: Útil para procesamiento continuo
3. **Backup**: Los CSV se guardan con timestamp, no se sobreescriben
4. **Base de Datos**: SQLite evita procesar el mismo correo dos veces
5. **Logs**: Revisar logs para entender qué está procesando

## 🆘 Ayuda Adicional

- **README Completo**: Ver `README.md`
- **Documentación**: Ver carpeta `docs/` (si existe)
- **Issues**: https://github.com/LuisVeraVR/medellin_sae/issues

## ✅ Checklist de Verificación

Antes de usar en producción:

- [ ] Credenciales configuradas correctamente
- [ ] Conexión IMAP funcionando
- [ ] Procesamiento manual exitoso
- [ ] CSV generado correctamente
- [ ] Logs sin errores críticos
- [ ] Modo automático configurado (si aplica)
- [ ] Backup del código

---

**Versión**: 1.0.0
**Última actualización**: 2024-11-30
