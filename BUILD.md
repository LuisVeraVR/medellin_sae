# Guía de Construcción e Instalación - Medellin SAE

Esta guía explica cómo crear un ejecutable y un instalador de Windows para distribuir **Medellin SAE** como un programa de escritorio profesional.

## 📋 Requisitos Previos

### Para Desarrollo
- Python 3.9 o superior
- pip (gestor de paquetes de Python)
- Git (opcional, para clonar el repositorio)

### Para Crear el Instalador (solo Windows)
- **PyInstaller** (incluido en requirements.txt)
- **Inno Setup 6**: [Descargar aquí](https://jrsoftware.org/isdl.php)

## 🚀 Proceso Completo

### Paso 1: Preparar el Entorno

```bash
# Clonar el repositorio (si aún no lo tienes)
git clone <url-del-repositorio>
cd medellin_sae

# Crear entorno virtual (recomendado)
python -m venv venv

# Activar entorno virtual
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

### Paso 2: Probar la Aplicación

Antes de crear el ejecutable, asegúrate de que la aplicación funciona correctamente:

```bash
python run.py
```

Verifica que:
- ✅ La aplicación se inicia correctamente
- ✅ Todas las tabs se muestran (Pulgarin, Somex, Productos Pulgarin, Configuración, Logs)
- ✅ Puedes importar productos desde Excel
- ✅ El procesamiento de facturas funciona

### Paso 3: Configurar Credenciales OAuth (Para Distribución)

**⚠️ IMPORTANTE:** Si quieres distribuir el ejecutable/instalador a la operativa con las credenciales de Azure AD ya configuradas, sigue estos pasos:

#### 3.1. Obtener Credenciales de Azure AD

Si aún no tienes las credenciales:

1. Ve a [Azure Portal](https://portal.azure.com)
2. **Azure Active Directory** → **App registrations** → **New registration**
3. Nombre: "Medellin SAE Production"
4. Supported account types: "Accounts in any organizational directory"
5. Redirect URI: Dejar en blanco (Device Code Flow)
6. Clic en **Register**
7. Copia el **Application (client) ID**
8. Copia el **Directory (tenant) ID** (o usa "common" para multi-tenant)

#### 3.2. Configurar en el Proyecto

```bash
# 1. Copiar el archivo de ejemplo
cp config/oauth_config.example.json config/oauth_config.json

# 2. Editar con tus credenciales
# Windows:
notepad config/oauth_config.json
# Linux/Mac:
nano config/oauth_config.json
```

#### 3.3. Editar oauth_config.json

Reemplaza `TU_AZURE_CLIENT_ID_AQUI` con tu Client ID real:

```json
{
  "azure_client_id": "12345678-1234-1234-1234-123456789abc",
  "azure_tenant_id": "common",
  "enabled": true,
  "description": "Configuración OAuth 2.0 para Office 365"
}
```

**Notas importantes:**
- ✅ Este archivo se embebe en el ejecutable al hacer build
- ✅ Los usuarios NO necesitan configurar nada
- ✅ Solo necesitan autenticarse con su cuenta de Office 365
- ⚠️ **NO** subas este archivo a Git (ya está en .gitignore)
- ⚠️ Guarda una copia segura de este archivo

#### 3.4. Verificar Configuración

```bash
# El archivo debe existir
ls -l config/oauth_config.json  # Linux/Mac
dir config\oauth_config.json    # Windows
```

#### Alternativa: Desarrollo Sin OAuth Config

Si solo quieres probar en desarrollo local, puedes usar el archivo `.env`:

```bash
# Crear .env
echo "AZURE_CLIENT_ID=tu-client-id" >> .env
echo "AZURE_TENANT_ID=common" >> .env
```

**Diferencia:**
- `.env` → Solo para desarrollo local
- `oauth_config.json` → Se incluye en el ejecutable para distribución

### Paso 4: Crear el Ejecutable

Ejecuta el script de build que creará un archivo `.exe` independiente:

```bash
python build.py
```

**¿Qué hace este comando?**
- Utiliza PyInstaller para empaquetar la aplicación
- Incluye todas las dependencias necesarias
- Crea un archivo ejecutable único (`MedellinSAE.exe`)
- Optimiza el tamaño del archivo

**Salida esperada:**
```
============================================================
Building MedellinSAE executable...
============================================================
Main script: C:\...\medellin_sae\src\main.py
Platform: win32

[PyInstaller output...]

============================================================
Build completed successfully!
============================================================
Executable: C:\...\medellin_sae\dist\MedellinSAE.exe
Size: XX.XX MB

Next steps:
1. Test the executable by running it
2. Create installer with: python create_installer.py
```

El ejecutable estará en: `dist/MedellinSAE.exe`

**Nota sobre oauth_config.json:**

Si el archivo `config/oauth_config.json` existe cuando ejecutas `build.py`, verás:
```
✓ Found oauth_config.json - will be included in executable
  This allows the executable to work without .env configuration
```

Si no existe, verás:
```
⚠ oauth_config.json not found - executable will require .env setup
  To include OAuth credentials in the executable:
  1. Copy config/oauth_config.example.json to config/oauth_config.json
  2. Edit oauth_config.json with your Azure AD credentials
  3. Run build.py again
```

### Paso 5: Probar el Ejecutable

Antes de crear el instalador, prueba el ejecutable:

```bash
cd dist
MedellinSAE.exe
```

Verifica que todo funciona igual que en modo desarrollo.

**Probar OAuth:**
1. Ve a Configuración
2. Ingresa un email de Office 365
3. Haz clic en "Autenticar con Office 365"
4. Debería abrir el navegador automáticamente
5. Si configuraste `oauth_config.json`, NO debería pedir configurar Azure

### Paso 6: Crear el Instalador (Windows)

#### 6.1. Instalar Inno Setup

1. Descarga Inno Setup 6: https://jrsoftware.org/isdl.php
2. Ejecuta el instalador
3. Instala con las opciones por defecto

#### 6.2. Generar el Instalador

```bash
python create_installer.py
```

**¿Qué hace este comando?**
- Verifica que existe `MedellinSAE.exe`
- Busca la instalación de Inno Setup
- Compila el script `installer.iss`
- Genera un instalador profesional de Windows

**Salida esperada:**
```
============================================================
Creando instalador de Windows...
============================================================
Inno Setup: C:\Program Files (x86)\Inno Setup 6\ISCC.exe
Script: C:\...\medellin_sae\installer.iss
Executable: C:\...\medellin_sae\dist\MedellinSAE.exe

[Inno Setup output...]

============================================================
Instalador creado exitosamente!
============================================================
Archivo: C:\...\medellin_sae\installer_output\MedellinSAE_Setup_v1.0.0.exe
Tamaño: XX.XX MB

Ahora puedes distribuir este instalador a los usuarios
```

El instalador estará en: `installer_output/MedellinSAE_Setup_v1.0.0.exe`

## 📦 Estructura del Instalador

El instalador creado incluye:

### Archivos Instalados
- `MedellinSAE.exe` - Ejecutable principal
- `README.md` - Documentación
- `version.txt` - Versión de la aplicación

### Directorios Creados
```
C:\Program Files\Medellin SAE\
├── MedellinSAE.exe
├── config\           (configuración de clientes)
├── data\             (base de datos SQLite)
├── output\           (CSVs generados)
├── logs\             (archivos de log)
└── LEAME.txt
```

### Accesos Directos
- **Menú de Inicio**: Medellin SAE
- **Escritorio**: Medellin SAE (opcional)
- **Carpetas útiles**:
  - Carpeta de Salida (Output)
  - Carpeta de Configuración
  - Logs

## 🎯 Características del Instalador

✅ **Instalación guiada**: Asistente visual en español/inglés
✅ **Detección de versión**: Actualiza o reinstala automáticamente
✅ **Desinstalador**: Limpia completamente la aplicación
✅ **Permisos**: Solicita permisos de administrador
✅ **Accesos directos**: Menú de inicio y escritorio
✅ **Profesional**: Interfaz moderna y limpia

## 🔧 Personalización

### Cambiar el Icono

1. Crea o obtén un archivo `icon.ico` (256x256 recomendado)
2. Colócalo en la raíz del proyecto
3. El build.py lo detectará automáticamente
4. Reconstruye: `python build.py`

### Cambiar la Versión

Edita `version.txt`:
```
v1.0.1
```

Luego reconstruye el ejecutable y el instalador.

### Modificar el Script de Instalación

Edita `installer.iss` para:
- Cambiar nombre de la empresa
- Agregar licencia
- Modificar directorios de instalación
- Personalizar mensajes

## 📤 Distribución

### Archivo a Distribuir

**Archivo**: `installer_output/MedellinSAE_Setup_v1.0.0.exe`

**Tamaño típico**: 80-150 MB (dependiendo de las dependencias)

### Requisitos del Usuario Final

- **Sistema Operativo**: Windows 7, 8, 10, 11 (64-bit)
- **Permisos**: Administrador (para instalación)
- **Espacio en disco**: ~200 MB
- **RAM**: Mínimo 2 GB (recomendado 4 GB)
- **Conexión a internet**: Para procesar correos electrónicos

### Primera Ejecución

Al ejecutar por primera vez, el usuario debe:

1. Configurar credenciales de email en la tab "Configuración"
2. Importar productos de Pulgarin (si aplica)
3. Verificar configuración de clientes en `config/clients.json`

## 🐛 Solución de Problemas

### Error: "No module named 'PyQt6'"
```bash
pip install -r requirements.txt
```

### Error: "ISCC.exe not found"
Instala Inno Setup desde: https://jrsoftware.org/isdl.php

### Error: "MedellinSAE.exe not found"
Primero ejecuta `python build.py` antes de crear el instalador.

### Ejecutable muy grande
- El tamaño es normal (incluye Python + todas las dependencias)
- PyInstaller crea ejecutables standalone completos
- Típicamente 80-150 MB es esperado

### Antivirus marca el ejecutable
- Es normal con ejecutables nuevos
- Firma digital (opcional): Requiere certificado de código
- Solución temporal: Agregar excepción en antivirus

## 📝 Notas Importantes

### Actualización de Versión

Para lanzar una nueva versión:

1. Actualiza `version.txt`:
   ```
   v1.1.0
   ```

2. Actualiza `installer.iss`:
   ```iss
   #define MyAppVersion "1.1.0"
   ```

3. Reconstruye todo:
   ```bash
   python build.py
   python create_installer.py
   ```

### Testing

**Siempre prueba**:
1. ✅ Ejecutable en una máquina limpia (sin Python)
2. ✅ Instalador completo
3. ✅ Desinstalador
4. ✅ Todas las funcionalidades principales

### Backup

Guarda copias de:
- El instalador generado
- El ejecutable
- Archivos de configuración

## 🔐 Firma Digital (Opcional)

Para distribución profesional, considera firmar digitalmente:

1. Obtén un certificado de firma de código
2. Usa `signtool.exe` para firmar el ejecutable
3. Firma también el instalador

Esto evita advertencias de Windows SmartScreen.

## 📧 Soporte

Para problemas durante el build:
1. Revisa los logs en consola
2. Verifica que todas las dependencias están instaladas
3. Asegúrate de tener la versión correcta de Python

## 🎉 ¡Listo!

Ahora tienes un instalador profesional de **Medellin SAE** listo para distribuir a los usuarios.

El instalador se encargará de:
- ✅ Instalar la aplicación
- ✅ Crear accesos directos
- ✅ Configurar directorios
- ✅ Permitir desinstalación limpia
