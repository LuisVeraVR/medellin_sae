# 🎯 Configuración para Correagro - SOLUCIÓN AL PROBLEMA

## ✅ DESCUBRIMIENTO IMPORTANTE

Tu empresa **NO usa Office 365 para IMAP**. Tienen su propio servidor de correo:

- **Servidor**: `imap.correagro.com`
- **IP**: 216.69.141.86
- **Puerto**: 993 (SSL)

Por eso la contraseña de aplicación de Microsoft NO funcionaba.

---

## 🚀 SOLUCIÓN EN 3 PASOS

### **Paso 1: Usar tu contraseña NORMAL de correo**

Edita el archivo `.env`:

```env
CORREAGRO_EMAIL=inteligenciadenegocios@correagro.com
CORREAGRO_PASSWORD=TuContraseñaNormalDeCorreo
```

⚠️ **NO uses la contraseña de aplicación de Microsoft** (`fptnqzqtsvrwxwvh`). Esa solo funciona con servidores de Microsoft.

---

### **Paso 2: Verificar configuración del servidor**

El archivo `config/clients.json` ya está configurado correctamente:

```json
{
  "email_config": {
    "search_criteria": "(UNSEEN SUBJECT \"COMERCIALIZADORA TRIPLE A\")",
    "imap_server": "imap.correagro.com"
  }
}
```

---

### **Paso 3: Probar conexión**

Ejecuta el script de prueba:

```bash
python test_correagro_imap.py
```

Ingresa tu **contraseña normal** cuando te la pida.

**Si funciona**, verás:
```
✅ ¡CONEXIÓN EXITOSA!
```

Luego ejecuta la aplicación:
```bash
python run.py
```

---

## 🔍 ¿Por qué fallaba antes?

1. ❌ **Servidor incorrecto**: Estabas intentando `outlook.office365.com`
2. ❌ **Contraseña incorrecta**: Usabas contraseña de aplicación de Microsoft
3. ✅ **Servidor correcto**: `imap.correagro.com`
4. ✅ **Contraseña correcta**: Tu contraseña normal de correo

---

## 📧 Diferencia entre servidores

| Servidor | Uso | Contraseña |
|----------|-----|------------|
| `outlook.office365.com` | Office 365 de Microsoft | Contraseña de aplicación |
| `imap.correagro.com` | Servidor propio de Correagro | Contraseña normal |

Correagro usa un servidor de correo propio (probablemente cPanel o Plesk), no Office 365 directamente.

---

## 🛠️ Si aún no funciona

### Opción 1: Verificar si IMAP está habilitado

Contacta al administrador de IT de Correagro:

```
Hola,

¿Puedes verificar si IMAP está habilitado para la cuenta:
inteligenciadenegocios@correagro.com?

Necesito acceso IMAP para automatizar el procesamiento de facturas.

Servidor que necesito usar: imap.correagro.com:993

Gracias!
```

### Opción 2: Verificar credenciales

1. Prueba iniciar sesión en el webmail de Correagro
2. Si no sabes la URL, prueba:
   - https://webmail.correagro.com
   - https://mail.correagro.com
   - https://correagro.com/webmail

3. Si puedes entrar al webmail pero NO funciona IMAP:
   - IMAP puede estar deshabilitado
   - Contacta al admin

### Opción 3: Revisar logs del servidor

Si tienes acceso al panel de control (cPanel, Plesk):
1. Busca logs de autenticación IMAP
2. Verifica si hay intentos fallidos
3. Puede haber restricciones de IP o geográficas

---

## 🎯 Configuración Completa Verificada

```env
# .env
CORREAGRO_EMAIL=inteligenciadenegocios@correagro.com
CORREAGRO_PASSWORD=TuContraseñaNormal  # ← NO la de aplicación de Microsoft
```

```json
// config/clients.json
{
  "clients": [
    {
      "id": "triple_a",
      "name": "Comercializadora Triple A",
      "enabled": true,
      "email_config": {
        "search_criteria": "(UNSEEN SUBJECT \"COMERCIALIZADORA TRIPLE A\")",
        "imap_server": "imap.correagro.com"  // ← Servidor correcto
      }
    }
  ]
}
```

---

## ✅ Checklist Final

Antes de ejecutar `python run.py`:

- [ ] Archivo `.env` tiene contraseña NORMAL (no de aplicación)
- [ ] `config/clients.json` tiene `"imap_server": "imap.correagro.com"`
- [ ] Ejecuté `python test_correagro_imap.py` y funcionó
- [ ] Puedo ver correos en el test
- [ ] Vi correos con "TRIPLE A" en el asunto

Si todo está ✅, ejecuta:
```bash
python run.py
```

---

## 📞 Soporte

Si después de esto sigue sin funcionar:

1. Ejecuta: `python test_correagro_imap.py` y copia el error exacto
2. Contacta al admin de IT de Correagro
3. Puede que IMAP esté bloqueado a nivel de servidor

---

**Última actualización**: 2024-11-30
