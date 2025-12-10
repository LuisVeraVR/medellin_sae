# Configuración OAuth 2.0 para Distribución

Esta guía explica cómo configurar las credenciales de Azure AD para que estén embebidas en el ejecutable, permitiendo distribuir la aplicación sin que los usuarios finales necesiten configurar nada.

## 🎯 Objetivo

Que el instalador/ejecutable funcione "out of the box" para la operativa:
- ✅ Usuarios solo ingresan su email
- ✅ Usuarios hacen clic en "Autenticar"
- ✅ NO necesitan configurar Azure AD
- ✅ NO necesitan crear archivos .env

## 📋 Requisitos Previos

1. Tener una aplicación registrada en Azure AD
2. Tener el Application (client) ID
3. Tener acceso a este proyecto para hacer el build

## 🚀 Proceso Completo

### Paso 1: Registrar Aplicación en Azure AD

Si aún no tienes una aplicación registrada:

1. **Ir a Azure Portal**
   - URL: https://portal.azure.com
   - Inicia sesión con cuenta administrativa

2. **Azure Active Directory**
   - Menú lateral → Azure Active Directory

3. **App registrations**
   - Clic en "App registrations"
   - Clic en "+ New registration"

4. **Configurar la Aplicación**
   - **Name**: `Medellin SAE Production`
   - **Supported account types**:
     - ✅ "Accounts in any organizational directory (Any Azure AD directory - Multitenant)"
   - **Redirect URI**:
     - Dejar en blanco (usamos Device Code Flow)
   - Clic en **Register**

5. **Copiar Credenciales**
   - Una vez creada, verás la página de la aplicación
   - Copia el **Application (client) ID** (UUID)
     - Ejemplo: `12345678-1234-1234-1234-123456789abc`
   - Copia el **Directory (tenant) ID** (o usa `common`)
     - `common` = multi-tenant (recomendado)
     - UUID = tenant específico

6. **Configurar Permisos (API permissions)**
   - Clic en "API permissions"
   - Verifica que tenga: `offline_access`, `IMAP.AccessAsUser.All`
   - Si no están, agrégalos:
     - Add a permission → Microsoft Graph → Delegated permissions
     - Busca y selecciona: `IMAP.AccessAsUser.All`
     - Busca y selecciona: `offline_access`
   - Clic en "Add permissions"
   - NO necesitas admin consent para estos permisos

7. **Configurar Authentication**
   - Clic en "Authentication"
   - En "Advanced settings"
   - Marca: ✅ "Allow public client flows"
   - Clic en "Save"

### Paso 2: Configurar en el Proyecto

```bash
# Navegar al proyecto
cd medellin_sae

# Copiar el archivo de ejemplo
cp config/oauth_config.example.json config/oauth_config.json

# Editar el archivo (Windows)
notepad config/oauth_config.json

# O editar (Linux/Mac)
nano config/oauth_config.json
```

### Paso 3: Editar oauth_config.json

Abre el archivo y reemplaza con tus credenciales:

```json
{
  "azure_client_id": "12345678-1234-1234-1234-123456789abc",
  "azure_tenant_id": "common",
  "enabled": true,
  "description": "Configuración OAuth 2.0 para Office 365"
}
```

**Campos:**
- `azure_client_id`: Tu Application (client) ID de Azure AD
- `azure_tenant_id`:
  - `"common"` para multi-tenant (recomendado)
  - O tu Tenant ID específico
- `enabled`: `true` para activar
- `description`: Comentario descriptivo

### Paso 4: Verificar Configuración

```bash
# Verificar que el archivo existe
ls -l config/oauth_config.json  # Linux/Mac
dir config\oauth_config.json    # Windows

# Verificar el contenido (NO mostrar en público)
cat config/oauth_config.json    # Linux/Mac
type config\oauth_config.json   # Windows
```

**Salida esperada:**
```json
{
  "azure_client_id": "12345678-...",
  "azure_tenant_id": "common",
  "enabled": true,
  "description": "Configuración OAuth 2.0 para Office 365"
}
```

⚠️ **Asegúrate de que NO sea el valor de ejemplo `TU_AZURE_CLIENT_ID_AQUI`**

### Paso 5: Build con OAuth Embebido

```bash
# Construir el ejecutable
python build.py
```

**Salida esperada:**
```
✓ Found oauth_config.json - will be included in executable
  This allows the executable to work without .env configuration

============================================================
Building MedellinSAE executable...
============================================================
...
```

Si ves esto, ¡perfecto! Las credenciales estarán embebidas.

Si ves:
```
⚠ oauth_config.json not found - executable will require .env setup
```

Significa que el archivo no existe o no está en `config/oauth_config.json`

### Paso 6: Probar el Ejecutable

```bash
cd dist
./MedellinSAE.exe  # Windows
./MedellinSAE      # Linux/Mac
```

**Prueba:**
1. Ve a la pestaña "Configuración"
2. Debería mostrar:
   - ✓ "Client ID configurado: 12345678..." (verde)
   - "Tenant ID: common"
3. Ingresa un email de Office 365
4. Clic en "🔐 Autenticar con Office 365"
5. Debería abrir el navegador automáticamente
6. **NO debería mostrar error de configuración**

## 🔒 Seguridad

### ✅ Buenas Prácticas

1. **NO subas oauth_config.json a Git**
   - Ya está en `.gitignore`
   - Verifica: `git status` no debe mostrarlo

2. **Guarda una copia segura**
   - Backup en un lugar seguro
   - Password manager
   - Documentación interna

3. **Limita el acceso**
   - Solo personal autorizado
   - No lo compartas públicamente

4. **Rotate credenciales periódicamente**
   - Cada 6-12 meses
   - Si hay breach de seguridad
   - Cuando personal sale de la empresa

### ⚠️ Qué NO Hacer

- ❌ NO subir a GitHub/GitLab
- ❌ NO enviar por email sin cifrar
- ❌ NO compartir en chat sin cifrar
- ❌ NO dejar en código fuente
- ❌ NO hardcodear en el código

## 🔄 Actualizar Credenciales

Si necesitas cambiar las credenciales:

1. **Editar oauth_config.json**
   ```bash
   notepad config/oauth_config.json
   ```

2. **Rebuild el ejecutable**
   ```bash
   python build.py
   ```

3. **Crear nuevo instalador**
   ```bash
   python create_installer.py
   ```

4. **Distribuir la nueva versión**
   - Incrementar versión en `version.txt`
   - Distribuir nuevo instalador

## 📚 Diferencias: .env vs oauth_config.json

| Aspecto | `.env` | `oauth_config.json` |
|---------|--------|---------------------|
| **Uso** | Desarrollo local | Producción/Distribución |
| **Ubicación** | Raíz del proyecto | `config/` |
| **Build** | NO incluido | SÍ incluido |
| **Git** | En `.gitignore` | En `.gitignore` |
| **Prioridad** | Alta (se lee primero) | Baja (fallback) |
| **Distribución** | NO distribuir | SÍ distribuir (embebido) |

## 🆘 Solución de Problemas

### Error: "AZURE_CLIENT_ID no está configurado"

**Causa:** No hay .env ni oauth_config.json

**Solución:**
```bash
# Opción 1: Crear oauth_config.json
cp config/oauth_config.example.json config/oauth_config.json
# Editar con tus credenciales
notepad config/oauth_config.json
# Rebuild
python build.py
```

### Error: "Client ID no configurado en .env" (en GUI)

**Causa:** La GUI no encuentra las credenciales

**Solución:**
1. Verifica que `config/oauth_config.json` existe
2. Verifica que contiene tu Client ID real
3. Verifica que `enabled: true`
4. Rebuild el ejecutable

### Instalador no incluye credenciales

**Causa:** oauth_config.json no existía cuando se hizo el build

**Solución:**
1. Crear/verificar `config/oauth_config.json`
2. `python build.py` (deberías ver "✓ Found oauth_config.json")
3. `python create_installer.py`

### Usuario final ve "Client ID no configurado"

**Causa:** El ejecutable no se buildeó con oauth_config.json

**Solución:**
1. Verificar en máquina de build:
   ```bash
   cat config/oauth_config.json
   ```
2. Verificar durante build:
   ```
   ✓ Found oauth_config.json
   ```
3. Si no aparece, crear el archivo y rebuild
4. Distribuir nuevo instalador

## ✅ Checklist Pre-Distribución

Antes de distribuir el instalador, verifica:

- [ ] `config/oauth_config.json` existe
- [ ] Contiene tu Client ID real (no el ejemplo)
- [ ] `enabled: true`
- [ ] NO está en Git (`git status` no lo muestra)
- [ ] Build muestra "✓ Found oauth_config.json"
- [ ] Probaste el ejecutable localmente
- [ ] OAuth funciona sin pedir configurar Azure
- [ ] Versión incrementada en `version.txt`
- [ ] Documentación actualizada
- [ ] Backup guardado de oauth_config.json

## 📞 Soporte

Si tienes problemas:

1. Revisa esta guía completa
2. Revisa `BUILD.md` para el proceso de build
3. Revisa los logs en `logs/app.log`
4. Contacta al administrador del sistema

---

**Última actualización:** Diciembre 2024
