# Guía de Configuración IMAP para Outlook/Office 365

## 🔴 Problema: "LOGIN failed"

Este error ocurre porque Microsoft ha deshabilitado la autenticación básica (usuario/contraseña) en muchas cuentas de Outlook. Necesitas seguir estos pasos:

---

## ✅ Solución 1: Habilitar IMAP en Outlook (REQUERIDO)

### Para cuentas personales (Outlook.com, Hotmail, Live):

1. Ve a **Outlook Web**: https://outlook.live.com/mail/
2. Haz clic en **⚙️ Configuración** (arriba a la derecha)
3. Click en **Ver toda la configuración**
4. Ve a **Correo** > **Sincronizar correo electrónico**
5. Busca **"Permitir que los dispositivos y aplicaciones usen IMAP"**
6. ✅ **ACTÍVALO**
7. Guarda cambios

### Para cuentas de trabajo/escuela (Office 365):

1. Ve a **Outlook Web**: https://outlook.office365.com/mail/
2. Haz clic en **⚙️ Configuración** (arriba a la derecha)
3. Click en **Ver toda la configuración**
4. Ve a **Correo** > **Sincronizar correo electrónico**
5. Busca **"Permitir que los dispositivos y aplicaciones usen IMAP"**
6. ✅ **ACTÍVALO**
7. Si no ves esta opción, tu administrador puede haberla deshabilitado (contacta a IT)

---

## ✅ Solución 2: Crear Contraseña de Aplicación (RECOMENDADO)

**⚠️ IMPORTANTE**: Si tienes verificación en 2 pasos activa, DEBES usar una contraseña de aplicación.

### Para cuentas personales:

1. Ve a: https://account.microsoft.com/security
2. Click en **Opciones de seguridad adicionales**
3. Desplázate a **Contraseñas de aplicación**
4. Click en **Crear una nueva contraseña de aplicación**
5. Nombra: `MedellinSAE`
6. **Copia la contraseña generada** (solo se muestra una vez)
7. Usa esta contraseña en lugar de tu contraseña normal

### Para cuentas de trabajo/escuela:

1. Ve a: https://mysignins.microsoft.com/security-info
2. Click en **+ Agregar método de inicio de sesión**
3. Selecciona **Contraseña de aplicación**
4. Nombra: `MedellinSAE`
5. **Copia la contraseña generada**
6. Usa esta contraseña en lugar de tu contraseña normal

**Ejemplo de contraseña de aplicación**: `abcd-efgh-ijkl-mnop`

---

## ✅ Solución 3: Verificar Configuración del Servidor

Asegúrate de usar estos datos correctos:

| Campo | Valor |
|-------|-------|
| **Servidor IMAP** | `outlook.office365.com` |
| **Puerto** | `993` |
| **Cifrado** | SSL/TLS |
| **Email** | tu_email@outlook.com |
| **Password** | ⚠️ Contraseña de aplicación (NO tu contraseña normal) |

---

## 🧪 Probar Conexión

Ejecuta el script de prueba:

```bash
python test_imap.py
```

Este script te ayudará a:
- ✅ Verificar si puedes conectarte al servidor
- ✅ Probar diferentes configuraciones
- ✅ Identificar el problema exacto

---

## 🔧 Pasos para Solucionar el Error "LOGIN failed"

### Opción 1: Usar Contraseña de Aplicación (MÁS COMÚN)

```bash
# 1. Crear contraseña de aplicación en Microsoft (ver arriba)

# 2. Actualizar archivo .env con la contraseña de aplicación:
CORREAGRO_EMAIL=tu_email@outlook.com
CORREAGRO_PASSWORD=abcd-efgh-ijkl-mnop  # ← Contraseña de aplicación

# 3. Ejecutar test_imap.py para verificar:
python test_imap.py

# 4. Si funciona, ejecutar la aplicación:
python run.py
```

### Opción 2: Habilitar Autenticación Básica (Solo Office 365 Empresarial)

Si eres administrador de Office 365:

1. Ve al **Centro de administración de Microsoft 365**: https://admin.microsoft.com
2. Configuración > Configuración de la organización > **Autenticación moderna**
3. Habilita **IMAP** para autenticación básica
4. Espera 24 horas para que los cambios se propaguen

⚠️ **No recomendado**: Microsoft está eliminando gradualmente la autenticación básica.

### Opción 3: Verificar Configuración de Seguridad

1. Verifica que no tengas políticas de seguridad que bloqueen IMAP
2. Verifica que tu cuenta no tenga restricciones de acceso desde aplicaciones de terceros
3. Si es cuenta empresarial, contacta a tu administrador de IT

---

## 📧 Configuración en el archivo .env

Después de crear la contraseña de aplicación:

```env
# .env
CORREAGRO_EMAIL=tu_email@outlook.com
CORREAGRO_PASSWORD=abcd-efgh-ijkl-mnop

# NO uses:
# CORREAGRO_PASSWORD=TuContraseñaNormal ❌
```

---

## ❓ Preguntas Frecuentes

### ¿Por qué no funciona mi contraseña normal?

Microsoft ha deshabilitado la autenticación básica (usuario/contraseña) por seguridad. Ahora requiere:
- Contraseñas de aplicación, o
- OAuth2 (autenticación moderna)

### ¿Dónde encuentro la opción "Contraseña de aplicación"?

Si no ves esta opción:
1. Puede que no tengas verificación en 2 pasos activada (actívala primero)
2. Tu administrador puede haberla deshabilitado
3. Tu cuenta puede no soportar contraseñas de aplicación

### ¿La contraseña de aplicación expira?

No, las contraseñas de aplicación no expiran a menos que:
- Las revoques manualmente
- Cambies tu contraseña principal
- Un administrador las revoque

### ¿Puedo usar OAuth2 en lugar de contraseña?

Sí, pero requiere cambios más complejos en el código. Por ahora, usa contraseñas de aplicación.

---

## 🆘 Si Nada Funciona

1. **Ejecuta el diagnóstico**:
   ```bash
   python test_imap.py
   ```

2. **Verifica los logs**:
   ```bash
   # En el archivo logs/app.log verás el error exacto
   ```

3. **Prueba con Gmail temporalmente** (para verificar que el código funciona):
   - Habilita IMAP en Gmail
   - Crea contraseña de aplicación en Google
   - Usa: `imap.gmail.com`

4. **Contacta a soporte de Microsoft**:
   - Soporte Outlook: https://support.microsoft.com/outlook
   - Comunidad: https://answers.microsoft.com

---

## ✅ Checklist de Verificación

Antes de ejecutar la aplicación:

- [ ] IMAP habilitado en Outlook Web
- [ ] Contraseña de aplicación creada (si tienes 2FA)
- [ ] Archivo .env actualizado con contraseña de aplicación
- [ ] test_imap.py ejecutado y funciona
- [ ] Servidor correcto: `outlook.office365.com`
- [ ] Puerto correcto: `993`

---

## 📝 Ejemplo Completo

```bash
# 1. Crear contraseña de aplicación en Microsoft
#    Resultado: abcd-efgh-ijkl-mnop

# 2. Actualizar .env
echo "CORREAGRO_EMAIL=luis@outlook.com" > .env
echo "CORREAGRO_PASSWORD=abcd-efgh-ijkl-mnop" >> .env

# 3. Probar conexión
python test_imap.py
# Ingresa: luis@outlook.com
# Ingresa: abcd-efgh-ijkl-mnop

# 4. Si funciona, ejecutar app
python run.py
```

---

**Última actualización**: 2024-11-30
