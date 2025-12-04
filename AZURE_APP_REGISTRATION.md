# Guía: Registro de Aplicación en Azure AD para OAuth 2.0

## 🎯 Objetivo
Registrar tu propia aplicación en Azure Active Directory para usar OAuth 2.0 con Office 365 IMAP.

## 📋 Prerrequisitos
- Cuenta de administrador de Azure/Office 365
- Acceso a https://portal.azure.com
- Permisos para registrar aplicaciones en tu tenant

---

## 🚀 Pasos para Registrar la Aplicación

### Paso 1: Acceder al Portal de Azure

1. Abre tu navegador y ve a: https://portal.azure.com
2. Inicia sesión con tu cuenta de administrador
3. En el buscador superior, escribe **"Azure Active Directory"** o **"Microsoft Entra ID"**
4. Haz clic en el servicio de Azure Active Directory

### Paso 2: Registrar Nueva Aplicación

1. En el menú lateral izquierdo, selecciona **"App registrations"** (Registros de aplicaciones)
2. Haz clic en **"+ New registration"** (Nuevo registro)
3. Completa el formulario:

   **Campos del formulario:**
   ```
   Name (Nombre):
   ├─ Medellin SAE - IMAP OAuth

   Supported account types (Tipos de cuenta compatibles):
   ├─ Selecciona: "Accounts in this organizational directory only"
   │  (Solo cuentas de este directorio organizativo)
   │  O si prefieres multi-tenant:
   └─ "Accounts in any organizational directory (Any Azure AD directory - Multitenant)"

   Redirect URI (URI de redirección):
   └─ Déjalo en blanco por ahora (Device Code Flow no lo necesita)
   ```

4. Haz clic en **"Register"** (Registrar)

### Paso 3: Copiar el Application (client) ID

Después de registrar, verás la página de **Overview** (Información general):

1. **COPIA** el valor de **"Application (client) ID"**
   - Ejemplo: `12345678-1234-1234-1234-123456789abc`
   - ⚠️ **GUÁRDALO** - Lo necesitarás para configurar la aplicación

2. **COPIA** también el **"Directory (tenant) ID"** (opcional, pero útil)
   - Ejemplo: `87654321-4321-4321-4321-cba987654321`

### Paso 4: Configurar Permisos de API

1. En el menú lateral izquierdo, selecciona **"API permissions"** (Permisos de API)
2. Haz clic en **"+ Add a permission"** (Agregar permiso)
3. Selecciona **"Office 365 Exchange Online"** o **"APIs my organization uses"**
4. Busca **"Office 365 Exchange Online"** en la lista
5. Selecciona **"Delegated permissions"** (Permisos delegados)
6. Busca y marca el checkbox:
   ```
   ✅ IMAP.AccessAsUser.All
   ```
7. Haz clic en **"Add permissions"** (Agregar permisos)

### Paso 5: Conceder Consentimiento de Administrador (IMPORTANTE)

1. Regresa a **"API permissions"** (Permisos de API)
2. Haz clic en **"✓ Grant admin consent for [Tu Organización]"**
   - (Conceder consentimiento de administrador)
3. Confirma haciendo clic en **"Yes"**
4. Verifica que aparezca un **checkmark verde** ✓ en la columna "Status"

   **Debería verse así:**
   ```
   Permission                    Type        Status
   ─────────────────────────────────────────────────
   IMAP.AccessAsUser.All         Delegated   ✓ Granted for [Org]
   ```

### Paso 6: Habilitar Public Client Flow

1. En el menú lateral izquierdo, selecciona **"Authentication"** (Autenticación)
2. Desplázate hasta la sección **"Advanced settings"** (Configuración avanzada)
3. En **"Allow public client flows"** (Permitir flujos de cliente público):
   ```
   Enable the following mobile and desktop flows:  ⚪ No  ⦿ Yes
   ```
4. Selecciona **"Yes"** (Sí)
5. Haz clic en **"Save"** (Guardar) en la parte superior

---

## 🔧 Configuración en la Aplicación Medellin SAE

### Paso 7: Actualizar archivo `.env`

1. Abre el archivo `.env` en la raíz del proyecto
2. Agrega las siguientes líneas con tu CLIENT_ID:

```env
# OAuth 2.0 Configuration (Azure AD App Registration)
AZURE_CLIENT_ID=12345678-1234-1234-1234-123456789abc  # ⬅️ REEMPLAZA con tu CLIENT_ID
AZURE_TENANT_ID=common  # Usa "common" para multi-tenant o tu Tenant ID específico
```

3. **Guarda** el archivo

### Paso 8: Probar la Configuración

Ejecuta el script de prueba:

```bash
python test_oauth_pulgarin.py
```

**Resultado esperado:**
- ✅ Muestra URL de verificación y código de dispositivo
- ✅ Te permite autenticarte con tu cuenta de Correagro
- ✅ Se conecta exitosamente a Office 365 IMAP
- ✅ Guarda el token en `data/oauth_token_cache.json`

---

## 🔍 Verificación de Permisos

### ¿Cómo verificar que todo está configurado correctamente?

En Azure Portal, ve a tu aplicación registrada:

**Checklist de configuración:**
```
✅ Application (client) ID copiado y agregado a .env
✅ API Permissions: IMAP.AccessAsUser.All agregado
✅ Admin consent: Granted (checkmark verde)
✅ Allow public client flows: Yes
```

---

## ❓ Solución de Problemas

### Error: "AADSTS65002: Consent between first party..."
- ❌ Estás usando el CLIENT_ID público de Microsoft
- ✅ Usa tu propio CLIENT_ID registrado en Azure AD

### Error: "AADSTS50020: User account... does not exist in tenant..."
- ❌ El TENANT_ID no es correcto
- ✅ Cambia AZURE_TENANT_ID a "common" en .env

### Error: "AADSTS7000218: The request body must contain the following parameter: 'client_assertion'..."
- ❌ "Allow public client flows" está en No
- ✅ Habilita "Allow public client flows" = Yes en Azure Portal

### Error: "AADSTS65001: The user or administrator has not consented..."
- ❌ No se concedió el consentimiento de administrador
- ✅ Ve a "API permissions" y haz clic en "Grant admin consent"

### Error: "IMAP authentication failed"
- ❌ IMAP no está habilitado en la cuenta
- ✅ Habilita IMAP en Outlook Web: Configuración > Correo > Sincronizar correo > IMAP

---

## 📚 Recursos Adicionales

- **Azure AD Portal**: https://portal.azure.com
- **Microsoft Graph Permissions Reference**: https://docs.microsoft.com/en-us/graph/permissions-reference
- **MSAL Python Documentation**: https://msal-python.readthedocs.io/
- **Device Code Flow**: https://docs.microsoft.com/en-us/azure/active-directory/develop/v2-oauth2-device-code

---

## 🆘 ¿Necesitas Ayuda?

Si tienes problemas:

1. Verifica que todos los checkboxes del checklist estén marcados
2. Ejecuta `python test_oauth_pulgarin.py` y revisa los logs
3. Elimina `data/oauth_token_cache.json` e intenta de nuevo
4. Verifica que el email en `.env` sea correcto
5. Asegúrate de tener permisos de administrador en Azure AD

---

**¡Listo!** Una vez completados estos pasos, tu aplicación Medellin SAE podrá usar OAuth 2.0 para conectarse a Office 365.
